from __future__ import annotations
from decimal import Decimal
import re
import json
import traceback
from django.contrib import messages
from django.db.models import Prefetch
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, TemplateView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import IntegrityError, transaction
from .forms import AddToCartForm, CheckoutForm
from .models import Cart, CartItem, Order, OrderItem, Product, ProductVariant
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# -------------------------
# Product catalogue
# -------------------------
class ProductListView(ListView):
    model = Product
    template_name = "shop/merch.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .prefetch_related("images")
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.filter(
                        is_active=True,
                        stock_qty__gt=0,  # ✅ aqui
                    ).order_by("size"),
                )
            )
        )

        if self.request.GET.get("featured") in ("1", "true", "yes"):
            qs = qs.filter(is_featured=True)

        return qs


class ProductDetailView(DetailView):
    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .prefetch_related("images")
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.filter(
                        is_active=True,
                        stock_qty__gt=0,   # ✅ aqui
                    ).order_by("size"),
                )
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["add_to_cart_form"] = AddToCartForm()
        return ctx


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@login_required
def checkout(request):
    """Página de checkout"""
    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    cart_items = cart.items.select_related('variant__product')
    total_price = cart.get_total_price()

    # Verificar se o carrinho está vazio
    if not cart_items:
        messages.error(request, 'O seu carrinho está vazio.')
        return redirect('shop:cart_detail')

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def cart_detail(request):
    try:
        cart = request.user.cart
        cart_items = cart.items.select_related(
            'variant__product'
        ).all()
        total_price = cart.get_total_price()
    except Cart.DoesNotExist:
        cart_items = []
        total_price = 0

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/cart_detail.html', context)


@login_required
@require_POST
def add_to_cart(request):
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    try:
        variant = ProductVariant.objects.get(id=variant_id, is_active=True)
    except ProductVariant.DoesNotExist:
        messages.error(request, "Produto não encontrado.")
        return redirect("shop:product_list")

    cart, _ = Cart.objects.get_or_create(user=request.user)

    if variant.stock_qty < quantity:
        msg = "Quantidade solicitada não disponível em estoque."
        messages.error(request, msg)
        if _is_ajax(request):
            return JsonResponse({"success": False, "message": msg})
        return redirect("shop:product_detail", slug=variant.product.slug)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={"quantity": min(quantity, variant.stock_qty)},
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > variant.stock_qty:
            messages.warning(request, f"Quantidade ajustada para o estoque disponível: {variant.stock_qty}.")
            cart_item.quantity = variant.stock_qty
        else:
            cart_item.quantity = new_quantity
        cart_item.save(update_fields=["quantity"])

    messages.success(request, f"{variant.product.name} adicionado ao carrinho!")

    if _is_ajax(request):
        return JsonResponse({
            "success": True,
            "cart_total_quantity": cart.get_total_quantity(),
            "message": f"{variant.product.name} adicionado ao carrinho!",
        })

    next_url = request.POST.get("next")  # opcional: permitir redirect para url absoluta
    if next_url:
        return redirect(next_url)
    return redirect("shop:cart_detail")


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    # AJAX
    if _is_ajax(request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "JSON inválido."}, status=400)

        quantity = payload.get("quantity", None)
        if quantity is None:
            return JsonResponse({"success": False, "message": "Quantidade não informada."}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse({"success": False, "message": "Quantidade inválida."}, status=400)

        # remover
        if quantity <= 0:
            cart = cart_item.cart
            cart_item.delete()
            return JsonResponse({
                "success": True,
                "removed": True,
                "quantity": 0,
                "item_total": "0.00",
                "cart_total": str(cart.get_total_price()),
                "cart_quantity": cart.get_total_quantity(),
            })

        # stock check
        available = cart_item.variant.stock_qty
        if quantity > available:
            # não grava; devolve o estado atual
            return JsonResponse({
                "success": False,
                "message": f"Quantidade não disponível. Estoque: {available}",
                "quantity": cart_item.quantity,  # quantidade REAL no DB
                "item_total": str(cart_item.get_total_price()),
                "cart_total": str(cart_item.cart.get_total_price()),
                "cart_quantity": cart_item.cart.get_total_quantity(),
            }, status=409)

        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])

        return JsonResponse({
            "success": True,
            "removed": False,
            "quantity": cart_item.quantity,  # quantidade gravada
            "item_total": str(cart_item.get_total_price()),
            "cart_total": str(cart_item.cart.get_total_price()),
            "cart_quantity": cart_item.cart.get_total_quantity(),
        })

    # fallback não-AJAX
    action = request.POST.get("action")
    if action == "update":
        quantity = int(request.POST.get("quantity", 1))
        if quantity > 0:
            if quantity > cart_item.variant.stock_qty:
                messages.error(request, f"Quantidade não disponível. Estoque: {cart_item.variant.stock_qty}")
            else:
                cart_item.quantity = quantity
                cart_item.save(update_fields=["quantity"])
                messages.success(request, "Quantidade atualizada!")
        else:
            cart_item.delete()
            messages.success(request, "Item removido do carrinho!")
    elif action == "remove":
        cart_item.delete()
        messages.success(request, "Item removido do carrinho!")

    return redirect("shop:cart_detail")


@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    cart_item.delete()

    if _is_ajax(request):
        return JsonResponse({
            "success": True,
            "cart_total": str(cart.get_total_price()),
            "cart_quantity": cart.get_total_quantity(),
            "message": "Item removido do carrinho!",
        })

    messages.success(request, "Item removido do carrinho!")
    return redirect("shop:cart_detail")


@login_required
@require_POST
def clear_cart(request):
    try:
        cart = request.user.cart
        cart_items_count = cart.items.count()
        cart.items.all().delete()
        messages.success(request, f"{cart_items_count} itens removidos do carrinho!")
    except Cart.DoesNotExist:
        pass

    return redirect("shop:cart_detail")


SHIPPING_FEES = {
    "pickup_store": Decimal("0.00"),
    "maputo": Decimal("250.00"),
    "local_delivery": Decimal("250.00"),
    "matola": Decimal("400.00"),
    "other_provinces": Decimal("1000.00"),
}


def _variant_final_price(variant) -> Decimal:
    getter = getattr(variant, "get_final_price", None)
    price = getter() if callable(getter) else getter
    return Decimal(str(price))


def _build_shipping_address(post) -> str:
    first_name = (post.get("first_name") or "").strip()
    last_name = (post.get("last_name") or "").strip()
    street = (post.get("street_address") or "").strip()
    city = (post.get("city") or "").strip()
    postal = (post.get("postal_code") or "").strip()
    country = (post.get("country") or "Moçambique").strip()

    full_name = " ".join([p for p in [first_name, last_name] if p]).strip()
    city_line = city + (f", {postal}" if postal else "")
    return "\n".join([l for l in [full_name, street, city_line, country] if l]).strip()


def _next_order_number_from_orders() -> str:
    """
    Gera PLA-0001, PLA-0002... sem tabela extra.
    Usa lock no último pedido e retry em colisão.
    """
    last = Order.objects.select_for_update().order_by("-id").first()
    if not last or not last.order_number:
        return "PLA-0001"

    m = re.search(r"PLA-(\d+)$", last.order_number.strip())
    if not m:
        # Se o formato antigo for diferente, recomeça a sequência.
        return "PLA-0001"

    n = int(m.group(1)) + 1
    return f"PLA-{n:04d}"


@login_required
def create_order(request):
    if request.method == 'POST':
        try:
            cart = request.user.cart
            cart_items = cart.items.select_related('variant__product').all()

            if not cart_items.exists():
                messages.error(request, 'O seu carrinho está vazio.')
                return redirect('shop:cart_detail')

            # Verificar stock
            for item in cart_items:
                variant = item.variant
                stock = getattr(variant, "stock_qty", None)
                if stock is None:
                    stock = getattr(variant, "stock_quantity", 0)

                if item.quantity > int(stock):
                    messages.error(
                        request,
                        f'Stock insuficiente para {variant.product.name} - {getattr(variant, "size", "")}'
                    )
                    return redirect('shop:cart_detail')

            # DELIVERY (ship/pickup) baseado no teu template
            delivery_type = (request.POST.get("delivery_type") or "ship").strip()

            if delivery_type == "pickup":
                fulfillment_method = Order.FulfillmentMethod.PICKUP
                delivery_fee = Decimal("0.00")

                pickup_location = (request.POST.get("pickup_location") or "").strip()
                if not pickup_location:
                    messages.error(request, "Selecione o ponto de levantamento.")
                    return redirect("shop:checkout")

                shipping_address = f"PICKUP: {pickup_location}"

            else:
                fulfillment_method = Order.FulfillmentMethod.DELIVERY
                shipping_method = (request.POST.get("shipping_method") or "").strip()

                if not shipping_method:
                    messages.error(request, "Selecione o método de envio.")
                    return redirect("shop:checkout")

                if shipping_method not in SHIPPING_FEES:
                    messages.error(request, "Método de envio inválido.")
                    return redirect("shop:checkout")

                delivery_fee = SHIPPING_FEES[shipping_method]
                shipping_address = _build_shipping_address(request.POST)

                if not shipping_address:
                    messages.error(request, "Morada é obrigatória para entrega.")
                    return redirect("shop:checkout")

            # Calcular subtotal/total (Decimal)
            subtotal = Decimal("0.00")
            for item in cart_items:
                subtotal += _variant_final_price(item.variant) * Decimal(item.quantity)

            total_amount = subtotal + delivery_fee

            # Dados do cliente (ajusta se tens campos no form)
            customer_email = (getattr(request.user, "email", "") or "").strip()
            if not customer_email:
                messages.error(request, "O utilizador não tem email. Defina um email no perfil.")
                return redirect("shop:checkout")

            first_name = (request.POST.get("first_name") or "").strip()
            last_name = (request.POST.get("last_name") or "").strip()
            customer_name = (" ".join([p for p in [first_name, last_name] if p]).strip()
                             or (request.user.get_full_name() or "Cliente"))
            customer_phone = (request.POST.get("customer_phone") or "").strip()

            # Criar encomenda com retry (sem classe nova)
            # Usa atomic aqui para garantir lock do select_for_update + criação
            with transaction.atomic():
                for _ in range(5):
                    order_number = _next_order_number_from_orders()

                    try:
                        order = Order.objects.create(
                            order_number=order_number,  # PLA-0001...
                            customer_name=customer_name,
                            customer_email=customer_email,
                            customer_phone=customer_phone,
                            fulfillment_method=fulfillment_method,
                            shipping_address=shipping_address,
                            status="pending",
                            subtotal_amount=subtotal,
                            delivery_fee=delivery_fee,
                            total_amount=total_amount,
                            placed_at=timezone.now(),
                        )
                        break
                    except IntegrityError:
                        # Colisão rara (ex: tabela vazia com concorrência). Re-tenta.
                        continue
                else:
                    raise Exception("Falha ao gerar número de encomenda único. Tente novamente.")

                # Criar itens + baixar stock
                for cart_item in cart_items:
                    variant = cart_item.variant
                    unit_price = _variant_final_price(variant)

                    OrderItem.objects.create(
                        order=order,
                        product_variant=variant,
                        quantity=cart_item.quantity,
                        unit_price=unit_price,
                        total_price=unit_price * Decimal(cart_item.quantity),
                    )

                    # Atualizar stock
                    if hasattr(variant, "stock_qty"):
                        variant.stock_qty = int(variant.stock_qty) - int(cart_item.quantity)
                        variant.save(update_fields=["stock_qty"])
                    else:
                        variant.stock_quantity = int(variant.stock_quantity) - int(cart_item.quantity)
                        variant.save(update_fields=["stock_quantity"])

                # Limpar carrinho
                cart.items.all().delete()

            messages.success(request, f'Encomenda #{order.order_number} criada com sucesso!')
            send_order_confirmation_email(order)
            return redirect('shop:cart_detail')

        except Exception as e:
            messages.error(request, f'Erro ao criar encomenda: {str(e)}')
            traceback.print_exc()
            return redirect('shop:checkout')

    return redirect('shop:cart_detail')


def send_order_confirmation_email(order):
    """
    Envia email de confirmação da encomenda para o cliente
    """
    try:
        subject = f'Confirmação da sua Encomenda #{order.order_number}'

        # Construir o contexto do email
        context = {
            'order': order,
            'customer_name': order.customer_name,
            'order_number': order.order_number,
            'order_date': order.placed_at,
            'subtotal': order.subtotal_amount,
            'delivery_fee': order.delivery_fee,
            'total_amount': order.total_amount,
            'shipping_address': order.shipping_address,
            'fulfillment_method': order.get_fulfillment_method_display(),
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
        }

        # Renderizar template HTML (crie um template em templates/emails/order_confirmation.html)
        html_message = render_to_string('shop/order_confirmation.html', context)

        # Versão texto simples (opcional)
        plain_message = strip_tags(html_message)

        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email="yuransaraiva.ys@gmail.com",
            recipient_list=[order.customer_email],
            html_message=html_message,
            fail_silently=False,
        )

        print(f"Email de confirmação enviado para {order.customer_email}")

    except Exception as e:
        print(f"Erro ao enviar email de confirmação: {str(e)}")
