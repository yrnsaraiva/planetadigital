from django.urls import path

from .models import Cart
from .views import (
    ProductListView, ProductDetailView, add_to_cart, cart_detail,
    clear_cart, update_cart_item, remove_from_cart, checkout, create_order
)

app_name = "shop"

urlpatterns = [
    path("merch/", ProductListView.as_view(), name="product_list"),
    path("merch/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),

    path("cart/", cart_detail, name="cart_detail"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/item/<int:item_id>/update/", update_cart_item, name="update_cart_item"),
    path("cart/item/<int:item_id>/remove/", remove_from_cart, name="remove_from_cart"),
    path("cart/clear/", clear_cart, name="clear_cart"),

    path("checkout/", checkout, name="checkout"),

    path('create-order/', create_order, name='create_order'),
]
