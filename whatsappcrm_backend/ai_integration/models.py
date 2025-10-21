from django.db import models
from django.core.exceptions import ValidationError

class AIProviderManager(models.Manager):
    def get_active_gemini_key(self):
        """
        Retrieves the active Google Gemini API key.
        Raises DoesNotExist if no active key is found.
        """
        try:
            provider = self.get(provider='google_gemini', is_active=True)
            return provider.api_key
        except self.model.DoesNotExist:
            raise self.model.DoesNotExist("No active 'google_gemini' provider found in the database.")
        except self.model.MultipleObjectsReturned:
            raise self.model.MultipleObjectsReturned("Multiple active 'google_gemini' providers found. Please ensure only one is active.")

class AIProvider(models.Model):
    """Stores credentials for various AI service providers."""
    PROVIDER_CHOICES = [
        ('google_gemini', 'Google Gemini'),
        # Add other providers here in the future
    ]

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    # IMPORTANT: In a production environment, this field should be encrypted.
    # Consider using a library like django-cryptography or a secrets manager like HashiCorp Vault.
    api_key = models.CharField(max_length=255, help_text="The API key for the provider.")
    is_active = models.BooleanField(default=False, help_text="Only one provider of each type should be active at a time.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # --- Rate Limiting Information (updated by tasks) ---
    rate_limit_limit = models.IntegerField(null=True, blank=True, help_text="The request limit per minute for this key.")
    rate_limit_remaining = models.IntegerField(null=True, blank=True, help_text="The number of remaining requests for the current window.")
    rate_limit_reset_time = models.DateTimeField(null=True, blank=True, help_text="The time when the rate limit window resets.")


    objects = AIProviderManager()

    def __str__(self):
        return f"{self.get_provider_display()} ({'Active' if self.is_active else 'Inactive'})"

    def clean(self):
        if self.is_active:
            if AIProvider.objects.filter(provider=self.provider, is_active=True).exclude(pk=self.pk).exists():
                raise ValidationError(f"An active provider for '{self.get_provider_display()}' already exists. Only one can be active.")