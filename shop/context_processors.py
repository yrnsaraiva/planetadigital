from decimal import Decimal
from .models import Cart


def cart_context(request):
    cart_data = {
        "count": 0,
        "total": "0",
        "pickup": "Triunfo, Maputo",
        "items": [],
    }

    if not request.user.is_authenticated:
        return {"cart": cart_data}

    try:
        cart = request.user.cart  # OneToOne (pode não existir)
    except Cart.DoesNotExist:
        return {"cart": cart_data}

    items_qs = cart.items.select_related("variant__product")
    cart_data["count"] = items_qs.count()
    cart_data["items"] = items_qs
    cart_data["total"] = str(cart.get_total_price())  # já tens esse método

    return {"cart": cart_data}
