from django.conf import settings
from django.core.exceptions import ValidationError


def _validate_image_size(file) -> None:
    max_size_mb = getattr(settings, 'MAX_IMAGE_SIZE_MB', 10)
    max_size_bytes = max_size_mb * 1024 *1024
    
    if file.size > max_size_bytes:
        raise ValidationError(f"IMAGE SHOULD NOT EXCEED {max_size_mb} MB.")    
    

def _validate_image_type(file)->None:
    allowed_types = getattr(
        settings, 
        'ALLOWED_IMAGE_TYPES', 
        ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    )
    
    content_type = file.content_type
    
    if content_type not in allowed_types:
        raise ValidationError(
            f"Invalid image type '{content_type}'. "
            f"Allowed types: {', '.join(allowed_types)}"
        )

def validate_image(file)->None:
    _validate_image_size(file)
    _validate_image_type(file)