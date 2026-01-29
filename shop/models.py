from decimal import Decimal
import uuid

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Product(models.Model):
    """
    Produto de merchandising.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or "product"
            candidate = base
            i = 2
            while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

        def get_main_image(self):
            """Retorna a primeira imagem do produto, se existir."""
            return self.images.first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="shop/products/")


class ProductVariant(models.Model):
    class Size(models.TextChoices):
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=4, choices=Size.choices)

    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    stock_qty = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "size"], name="uniq_product_size"),
        ]

    def get_final_price(self):
        """Retorna o preço específico da variante ou usa o preço do produto."""
        if self.price_override is not None:
            return self.price_override
        # Usar o preço do produto como fallback
        return self.product.price

    def __str__(self):
        return f"{self.product.name} - {self.size}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    session_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        total = Decimal('0.00')  # Iniciar com Decimal
        for item in self.items.all():
            total += item.get_total_price()
        return total

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "variant"], name="uniq_cart_variant"),
        ]

    def get_total_price(self):
        # Garantir que retorna Decimal
        price = self.variant.get_final_price()
        if isinstance(price, (int, float)):
            price = Decimal(str(price))
        return price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.variant}"


class Order(models.Model):
    class FulfillmentMethod(models.TextChoices):
        DELIVERY = "delivery", "Delivery"
        PICKUP = "pickup", "Pickup"

    order_number = models.CharField(max_length=32, unique=True, db_index=True)

    customer_name = models.CharField(max_length=180)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=40, blank=True)

    fulfillment_method = models.CharField(
        max_length=20,
        choices=FulfillmentMethod.choices,
        default=FulfillmentMethod.DELIVERY,
        db_index=True,
    )

    # Para DELIVERY:
    shipping_address = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        db_index=True,
    )

    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    placed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(_('preço total'), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('item de encomenda')
        verbose_name_plural = _('itens de encomenda')

    def __str__(self):
        return f"{self.quantity} x {self.product_variant}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
