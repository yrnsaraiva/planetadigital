from django.urls import path
from .views import SignupView, LoginView, LogoutView, OrderListView, OrderConfirmView, OrderCancelView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path('orders/', OrderListView.as_view(), name='orders'),


    path('orders/<str:order_number>/confirm/', OrderConfirmView.as_view(), name='order_confirm'),
    path('orders/<str:order_number>/cancel/', OrderCancelView.as_view(), name='order_cancel'),
]
