from django.urls import path
from .views import list_campaigns, campaign_detail

app_name = "campaigns"

urlpatterns = [

    path("", list_campaigns, name="list_campaigns"),
    path('<slug:slug>/', campaign_detail, name='campaign_detail'),
]
