from django.db import models
from django.core.validators import validate_email


class NewsletterSubscriber(models.Model):
    """
    Subscrição simples de newsletter.
    """
    class Status(models.TextChoices):
        SUBSCRIBED = "subscribed", "Subscribed"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    email = models.EmailField(unique=True, validators=[validate_email])
    name = models.CharField(max_length=120, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBSCRIBED,
        db_index=True,
    )

    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email