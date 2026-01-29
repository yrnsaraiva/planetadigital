from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    """
    Evento PLANETA.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    poster = models.ImageField(upload_to="events/posters/")
    description = models.TextField()

    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(null=True, blank=True)

    city = models.CharField(max_length=120)

    lineup_text = models.TextField(blank=True)

    ticket_url = models.URLField(blank=True)

    is_featured = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_at",)
        indexes = [
            models.Index(fields=["-start_at"]),
            models.Index(fields=["is_featured", "-start_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "event"
            candidate = base
            i = 2
            while Event.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        return self.start_at >= timezone.now()

    @property
    def is_past(self):
        return self.start_at < timezone.now()


class EventMedia(models.Model):
    """
    Fotos e vídeos pós-evento.
    """
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="media_items",
    )

    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="events/media/")
    caption = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["event",]),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.media_type}"
