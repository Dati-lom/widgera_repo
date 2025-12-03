import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

_logger = logging.getLogger(__name__)


@dataclass
class StorageUploadResult:
    url: str
    storage_path: str | None
    backend: str  # 's3' or 'local'


class StorageService:
    def __init__(self):
        self.use_s3 = getattr(settings, 'USE_S3', True)
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '').strip()
        _logger.info(f"STORAGE SERVICE INIT USE_S3={self.use_s3} BUCKET={self.bucket_name}")
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        self.s3_client = None

    def _ensure_s3_client(self):
        if self.s3_client:
            return self.s3_client

        if not self.use_s3:
            raise RuntimeError('S3 uploads are disabled. Set USE_S3=True to enable.')

        access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '').strip()
        secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '').strip()
        
        #very careful logging
        _logger.debug("ESSENTIALS FETCHED FOR S3 CLIENT %s \n %s", access_key[:4] + '...' if access_key else 'MISSING',
                      secret_key[:4] + '...' if secret_key else 'MISSING')

        if not all([access_key, secret_key, self.bucket_name]):
            raise RuntimeError('AWS credentials or bucket name missing; check settings.')

        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError('boto3 is required for S3 uploads.') from exc

        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region or 'us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            _logger.info('S3 client initialised for bucket=%s', self.bucket_name)
        except Exception as exc:  # noqa: BLE001
            _logger.error('Failed to create S3 client: %s', exc)
            raise RuntimeError('Failed to initialise S3 client') from exc

        return self.s3_client
        
    def _generate_unique_filename(self, filename: str) -> str:
        unique_id = uuid.uuid4().hex
        file_extension = Path(filename).suffix
        return f"{unique_id}{file_extension}"        
    
    def _upload_to_local(self, file_content, filename, content_type=None) -> StorageUploadResult:
        file_path = f"images/{filename}"
        
        #save using djano default
        saved_path = default_storage.save(file_path, ContentFile(file_content))
        
        url = f"{settings.MEDIA_URL}{saved_path}"
        
        _logger.info(f"SAVED FILE HERER {url}")
        return StorageUploadResult(url=url, storage_path=saved_path, backend='local')
    
    def _upload_to_s3(self, file_content, filename, content_type) -> StorageUploadResult:
        #io.BytesIO to manage file content as streams
        from io import BytesIO
        
        s3_key = f"images/{filename}"
        
        _logger.info(f"UPLOADING FILE TO S3 AT KEY: {s3_key}")
        try:
            client = self._ensure_s3_client()
            #s3 upload
            client.upload_fileobj(
                BytesIO(file_content),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                }
            )
            region = self.region or 'us-east-1'
            url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            _logger.info(f"FILE UPLOADED TO S3: {s3_key}")
            return StorageUploadResult(url=url, storage_path=None, backend='s3')
            
        except Exception as e:
            _logger.error(f"S3 UPLOAD FAILED: {e}")
            raise RuntimeError(f"FAILED TO UPLOAD FILE: {e}")
        
        
    def upload_image(self, file_content, original_filename,content_type="image/jpeg") -> StorageUploadResult:
        #get filename
        filename = self._generate_unique_filename(original_filename)
        
        _logger.info(f"GOT FILE AND CHANGED NAME TO {filename}")
        
        if self.use_s3:
            _logger.info("UPLOADING TO S3")
            result = self._upload_to_s3(file_content, filename,content_type)
        else:
            result = self._upload_to_local(file_content, filename, content_type)
        return result
    
    
    #add delete later
    


storage_service = StorageService()

