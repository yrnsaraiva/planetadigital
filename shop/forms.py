from django import forms
from .models import Order


class AddToCartForm(forms.Form):
    variant_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1)


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=180)
    customer_email = forms.EmailField()
    customer_phone = forms.CharField(max_length=40, required=False)

    fulfillment_method = forms.ChoiceField(choices=Order.FulfillmentMethod.choices)

    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("fulfillment_method")
        addr = (cleaned.get("shipping_address") or "").strip()

        if method == Order.FulfillmentMethod.DELIVERY and not addr:
            self.add_error("shipping_address", "Morada é obrigatória para entrega.")

        return cleaned
