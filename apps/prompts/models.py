from django.conf import settings
from django.db import models


#promt schema model for history
class PromptSchema(models.Model):
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

#Field definition for prompt schema
class SchemaField(models.Model):
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
    return f"users/{instance.user_id}/uploads/{filename}"

#image for history
class UploadedImage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_images'
    )
    file = models.ImageField(upload_to=user_image_upload_to, blank=True, null=True)
    image_url = models.URLField(blank=True)
    checksum = models.CharField(max_length=64)
    original_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_hash(file_content: bytes) -> str:
        import hashlib

        sha256 = hashlib.sha256()
        sha256.update(file_content)
        return sha256.hexdigest()

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

#prompt execution history
class PromptExecution(models.Model):
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
