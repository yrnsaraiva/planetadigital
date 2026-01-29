def cart_context(request):
    cart = {
        "count": 0,
        "total": "0",
        "pickup": "Triunfo, Maputo",
        "items": [],
    }
    return {"cart": cart}
