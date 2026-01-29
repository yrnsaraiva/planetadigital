from django.urls import path
from .views import EventsListView,EventDetailView

app_name = "eventos"

urlpatterns = [

    path("agenda/", EventsListView.as_view(), name="agenda"),
    path("agenda/<slug:slug>/", EventDetailView.as_view(), name="detail"),

]
