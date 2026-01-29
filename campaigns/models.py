from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Campaign(models.Model):
    """
    Campanha beneficente promovida pela PLANETA.
    Ex: doações, ações sociais, apoio comunitário.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        FINISHED = "finished", "Finished"

    title = models.CharField(
        max_length=200,
        help_text="Título público da campanha"
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        db_index=True
    )

    cover_image = models.ImageField(
        upload_to="campaigns/covers/",
        help_text="Imagem principal da campanha"
    )

    short_description = models.CharField(
        max_length=300,
        help_text="Resumo curto para cards e listagens"
    )

    description = models.TextField(
        help_text="Descrição completa da campanha, objetivos e impacto esperado"
    )

    call_to_action = models.CharField(
        max_length=120,
        blank=True,
        help_text="Ex: Doe agora, Participe, Saiba mais"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )

    start_date = models.DateField(
        default=timezone.now,
        db_index=True
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Opcional: data de encerramento"
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Destacar na homepage ou secção principal",
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_date",)
        indexes = [
            models.Index(fields=["status", "start_date"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "campaign.html"
            candidate = base
            i = 2
            while Campaign.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        today = timezone.now().date()
        if self.status != self.Status.ACTIVE:
            return False
        if self.end_date and self.end_date < today:
            return False
        return self.start_date <= today
