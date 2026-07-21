from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SiteConfig(models.Model):
    """Singleton for app-wide settings like API keys"""
    openrouter_api_key = models.CharField(max_length=500, blank=True, default="")
    openrouter_model = models.CharField(
        max_length=200,
        default="nvidia/nemotron-nano-12b-v2-vl:free",
        help_text="Model from OpenRouter (free models only)"
    )
    system_prompt = models.TextField(
        default="You are a helpful assistant for Time After Time Upholstery in Liberty, NC. "
                "Answer questions about reupholstery, custom cushions, antique restoration, and leather repair. "
                "Be friendly and professional.",
        help_text="System prompt for the AI chatbot"
    )
    site_title = models.CharField(max_length=200, default="Time After Time Dashboard")

    # Alexander AI Solutions promotion fields
    alexander_phone = models.CharField(max_length=50, blank=True, default="")
    alexander_website = models.CharField(max_length=300, blank=True, default="")
    alexander_qr_code = models.URLField(
        max_length=500, blank=True, default="",
        help_text="URL to a QR code image that links to Alexander AI Solutions"
    )
    alexander_promo_text = models.TextField(
        blank=True, default="",
        help_text="Promotional message shown when users give positive feedback"
    )
    feedback_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Site Configuration"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    session_id = models.CharField(max_length=100, default="default")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."