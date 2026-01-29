from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from shop.models import Order, OrderItem
from django.db.models import Prefetch
from django.http import JsonResponse

from .forms import SignupForm, EmailLoginForm


class SignupView(View):
    template_name = "accounts/signup.html"

    def get(self, request):
        return render(request, self.template_name, {"form": SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = form.save()
        login(request, user)
        return redirect(request.GET.get("next") or reverse("shop:product_list"))


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": EmailLoginForm()})

    def post(self, request):
        form = EmailLoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].lower()
        password = form.cleaned_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email ou password inválidos.")
            return render(request, self.template_name, {"form": form})

        user = authenticate(
            request,
            username=user.username,
            password=password,
        )

        if user is None:
            messages.error(request, "Email ou password inválidos.")
            return render(request, self.template_name, {"form": form})

        login(request, user)
        return redirect(request.GET.get("next") or reverse("shop:product_list"))


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect(reverse("accounts:login"))


class OrderListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(
            customer_email=self.request.user.email
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related(
                    'product_variant__product'
                ).prefetch_related('product_variant__product__images')
            )
        ).order_by('-created_at')


class OrderConfirmView(LoginRequiredMixin, View):
    def post(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number,
                customer_email=request.user.email
            )

            if order.status == 'pending':
                order.status = 'confirmed'
                order.save(update_fields=['status'])
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Pedido já processado'})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Pedido não encontrado'})


class OrderCancelView(LoginRequiredMixin, View):
    def post(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number,
                customer_email=request.user.email
            )

            if order.status == 'pending':
                order.status = 'cancelled'
                order.save(update_fields=['status'])
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Não é possível cancelar este pedido'})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Pedido não encontrado'})