import logging
from dataclasses import dataclass
from typing import Optional

from django.core.files.uploadedfile import UploadedFile

from apps.prompts.models import UploadedImage
from apps.prompts.utils.validators import validate_image
from .storage_service import storage_service

logger = logging.getLogger(__name__)


#simplified class for data store
@dataclass
class ImageUploadResult:
    image: UploadedImage
    is_duplicate: bool
    message: str


class ImageHandler:
    def handle_upload(self, user, file: UploadedFile) -> ImageUploadResult:

        # IMAGE VALIDATTION
        logger.debug(f"Validating image: {file.name}")
        validate_image(file)
        
        # hash calculations        
        file_content = file.read()
        logger.debug(f"Read {len(file_content)} bytes from uploaded file")
        file_hash = UploadedImage.calculate_hash(file_content=file_content)
        
        logger.debug(f"Image hash: {file_hash[:16]}...")
        
        # DUP CHECK
        existing_image = self._find_duplicate(user, file_hash)
        
        if existing_image:
            logger.info(
                f"DUPLICATE IMAGE FOUND FOR: {user.id}: {existing_image.id}"
            )
            return ImageUploadResult(
                image=existing_image,
                is_duplicate=True,
                message="ALREADY EXISTS"
            )
        
        # STORE IN STORAGE + DB (for history and stuff)
        logger.debug(f"Uploading image for user {user.id} to configured storage")
        storage_result = storage_service.upload_image(
            file_content=file_content,
            original_filename=file.name,
            content_type=file.content_type,
        )

        image_kwargs = {
            'user': user,
            'checksum': file_hash,
            'original_filename': file.name,
        }

        if storage_result.backend == 's3':
            image_kwargs['image_url'] = storage_result.url
        else:
            if storage_result.storage_path:
                image_kwargs['file'] = storage_result.storage_path
            image_kwargs['image_url'] = storage_result.url

        uploaded_image = UploadedImage.objects.create(**image_kwargs)
        
        logger.info(
            f"New image uploaded: {uploaded_image.id} for user {user.id}"
        )
        
        #RESULT
        return ImageUploadResult(
            image=uploaded_image,
            is_duplicate=False,
            message="Image uploaded successfully"
        )
    
    def _find_duplicate(self, user, file_hash) -> Optional[UploadedImage]:
        return (
            UploadedImage.objects
            .filter(user=user, checksum=file_hash)
            .first()
        )
    
    def get_user_images(self, user, limit: Optional[int] = None):
        queryset = UploadedImage.objects.filter(user=user)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset

image_handler = ImageHandler()