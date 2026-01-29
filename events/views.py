from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView, DetailView

from .models import Event


class EventsListView(TemplateView):
    """
    Página de agenda:
    - Próximos eventos
    - Eventos passados (arquivo)
    Filtros opcionais via querystring:
      ?q=texto  (title, city, description, lineup_text)
      ?city=Maputo
      ?featured=1
    """
    template_name = "events/events.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        now = timezone.now()

        q = (self.request.GET.get("q") or "").strip()
        city = (self.request.GET.get("city") or "").strip()
        featured = (self.request.GET.get("featured") or "").strip()

        base = Event.objects.all()

        if q:
            base = base.filter(
                Q(title__icontains=q) |
                Q(city__icontains=q) |
                Q(description__icontains=q) |
                Q(lineup_text__icontains=q)
            )

        if city:
            base = base.filter(city__iexact=city)

        if featured in ("1", "true", "yes", "on"):
            base = base.filter(is_featured=True)

        upcoming = (
            base.filter(start_at__gte=now)
            .order_by("start_at")
        )
        past = (
            base.filter(start_at__lt=now)
            .order_by("-start_at")
        )

        featured_event = (
            Event.objects.filter(is_featured=True, start_at__gte=now)
            .order_by("start_at")
            .first()
        ) or (
            Event.objects.filter(is_featured=True, start_at__lt=now)
            .order_by("-start_at")
            .first()
        )

        cities = (
            Event.objects.exclude(city__isnull=True)
            .exclude(city__exact="")
            .values_list("city", flat=True)
            .distinct()
            .order_by("city")
        )

        ctx.update(
            q=q,
            city=city,
            featured=featured,
            featured_event=featured_event,
            upcoming_events=upcoming,
            past_events=past,
            cities=list(cities),
            now=now,
        )
        return ctx


class EventDetailView(DetailView):
    """
    Detalhe do evento por slug.
    Inclui media_items (EventMedia) via prefetch.
    """
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Event.objects.all()
            .prefetch_related("media_items")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()

        # Próximos eventos (sidebar)
        related_upcoming = (
            Event.objects.filter(start_at__gte=now)
            .exclude(pk=self.object.pk)
            .order_by("start_at")[:6]
        )

        # Últimos eventos (arquivo)
        related_recent = (
            Event.objects.filter(start_at__lt=now)
            .exclude(pk=self.object.pk)
            .order_by("-start_at")[:6]
        )

        ctx.update(
            now=now,
            related_upcoming=related_upcoming,
            related_recent=related_recent,
        )
        return ctx
