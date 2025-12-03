from django.conf import settings
from django.db import models


class PromptSchema(models.Model):
    """Reusable schema that stores the structure of an LLM response."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prompt_schemas'
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self) -> str:  # pragma: no cover - readability only
        return f"{self.name} ({self.user.username})"


class SchemaField(models.Model):
    """Field definition for a schema."""

    class FieldType(models.TextChoices):
        STRING = 'string', 'String'
        NUMBER = 'number', 'Number'

    schema = models.ForeignKey(
        PromptSchema,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    name = models.CharField(max_length=120)
    field_type = models.CharField(
        max_length=16,
        choices=FieldType.choices,
        default=FieldType.STRING
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('schema', 'name')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:  # pragma: no cover - readability only
        return f"{self.schema.name}:{self.name} ({self.field_type})"


def user_image_upload_to(instance: 'UploadedImage', filename: str) -> str:
    """Group uploads per user so S3 or local storage remains tidy."""
    return f"users/{instance.user_id}/uploads/{filename}"


class UploadedImage(models.Model):
    """Image uploaded by the user for prompt executions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_images'
    )
    file = models.ImageField(upload_to=user_image_upload_to)
    checksum = models.CharField(max_length=64)
    original_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'checksum'],
                name='unique_user_image_checksum'
            )
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover - readability only
        return f"Image {self.id} for {self.user.username}"


class PromptExecution(models.Model):
    """Prompt + schema + image execution tracked per user."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prompt_executions'
    )
    schema = models.ForeignKey(
        PromptSchema,
        on_delete=models.SET_NULL,
        related_name='executions',
        null=True,
        blank=True
    )
    image = models.ForeignKey(
        UploadedImage,
        on_delete=models.SET_NULL,
        related_name='executions',
        null=True,
        blank=True
    )
    prompt_text = models.TextField()
    structured_fields = models.JSONField(default=list, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover - readability only
        return f"Execution {self.id} ({self.status})"
