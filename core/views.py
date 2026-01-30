from django.shortcuts import render
from shop.models import OrderItem, Cart
from events.models import Event
from django.db.models import Sum
from django.utils import timezone


def buscar_nr_itens_cart(request):
    try:
        cart = request.user.cart
        cart_items = cart.items.select_related(
            'variant__product'
        ).all()
    except Cart.DoesNotExist:
        cart_items = []

    return cart_items


def index(request):
    from shop.models import Product

    top_product = Product.objects.filter(is_featured=True).first()

    now = timezone.now()

    evento_mais_proximo = (
        Event.objects
        .filter(start_at__gte=now)
        .order_by("start_at")
        .first()
    )

    ctx = {
        'top_product': top_product,
        'e': evento_mais_proximo,
        'cart_items': buscar_nr_itens_cart(request)
    }

    return render(request, 'core/index.html', context=ctx)


def about(request):

    ctx = {'cart_items': buscar_nr_itens_cart(request)}

    return render(request, 'core/universe.html', context=ctx)


def contact(request):

    ctx = {'cart_items': buscar_nr_itens_cart(request)}

    return render(request, 'core/contacto.html', context=ctx)