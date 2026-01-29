from django.contrib import admin
from django.db.models import Sum

from .models import (
    Product,
    ProductImage,
    ProductVariant,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image",)
    ordering = ("id",)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("size", "price_override", "stock_qty", "is_active")
    ordering = ("size",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active", "is_featured", "created_at")
    list_filter = ("is_active", "is_featured", "created_at")
    search_fields = ("name", "description", "slug")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        ("Produto", {"fields": ("name", "slug", "description")}),
        ("Preço & Estado", {"fields": ("price", "is_active", "is_featured")}),
        ("Datas", {"fields": ("created_at",)}),
    )

    inlines = (ProductImageInline, ProductVariantInline)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "effective_price_display", "stock_qty", "is_active")
    list_filter = ("size", "is_active", "product")
    search_fields = ("product__name", "product__slug")
    ordering = ("product", "size")

    def effective_price_display(self, obj: ProductVariant):
        return obj.effective_price()
    effective_price_display.short_description = "Effective price"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("variant", "quantity")
    autocomplete_fields = ("variant",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at", "items_count")
    search_fields = ("session_key", "user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = (CartItemInline,)

    def items_count(self, obj: Cart):
        return obj.items.count()
    items_count.short_description = "Items"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity")
    list_filter = ("cart",)
    search_fields = ("cart__session_key", "variant__product__name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("unit_price", "quantity", "total_price")
    readonly_fields = ("total_price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "customer_email",
        "status",
        "subtotal_amount",
        "delivery_fee",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "created_at", "fulfillment_method")
    search_fields = ("order_number", "customer_name", "customer_email", "customer_phone", "shipping_address")
    ordering = ("-created_at",)
    readonly_fields = ("order_number", "created_at", "subtotal_amount", "delivery_fee", "total_amount")

    fieldsets = (
        ("Identificação", {"fields": ("order_number", "created_at", "placed_at")}),
        ("Cliente", {"fields": ("customer_name", "customer_email", "customer_phone")}),
        ("Entrega / Levantamento", {"fields": ("fulfillment_method", "shipping_address")}),
        ("Estado", {"fields": ("status",)}),
        ("Totais", {"fields": ("subtotal_amount", "delivery_fee", "total_amount")}),
    )

    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_variant", "unit_price", "quantity", "total_price")
    search_fields = ("order__order_number", "product_variant__product__name")
    ordering = ("-id",)
