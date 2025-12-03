import logging
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

_logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.user_s3 = getattr(default_storage, 'USE_S3', None)
        #initialize client
        
        self.s3_client = self._init_s3_client
        
    
    
    def _init_s3_client(self) -> None:
        try:
            #AWS
            import boto3
            
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secre_access_key = settings.AWS_SECRET_ACCESS_KEY,
                region_name= settings.AWS_S3_REGION_NAME if not "" else 'us-east-1'
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            _logger.info("S3 SUCCESS INIT")
        except Exception as e:
            _logger.info(f"ERROR S3 INIT: {e} ")
            raise RuntimeError("FAILED TO INIT S3") from e
        
    def _generate_unique_filename(self, filename: str) -> str:
        unique_id = uuid.uuid4().hex
        file_extension = Path(filename).suffix
        return f"{unique_id}{file_extension}"        
    
    def _upload_to_local(self, file_content,filename)->str:
        file_path = f"images/{filename}"
        
        #save using djano default
        saved_path = default_storage.save(file_path, ContentFile(file_content))
        
        url = f"{settings.MEDIA_URL}{saved_path}"
        
        _logger.info(f"SAVED FILE HERER {url}")
        return url
    
    def _upload_to_s3(self,file_content,filename,content_type)->str:
        #io.BytesIO to manage file content as streams
        from io import BytesIO
        
        s3_key = f"images/{filename}"
        
        try:
            #s3 upload
            self.s3_client.upload_fileobj(
                BytesIO(file_content),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'
                }
            )
            region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            url = f"https://{self. bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            _logger.info(f"FILE UPLOADED TO S3: {s3_key}")
            return url
            
        except Exception as e:
            _logger.error(f"S3 UPLOAD FAILED: {e}")
            raise RuntimeError(f"FAILED TO UPLOAD FILE: {e}")
        
        
    def upload_image(self, file_content, original_filename,content_type="image/jpeg")->str:
        #get filename
        filename = self._generate_unique_filename(original_filename)
        
        _logger.info(f"GOT FILE AND CHANGED NAME TO {filename}")
        
        if self.user_s3:
            url = self._upload_to_s3(file_content, filename,content_type)
        else:
            url = self._upload_to_local(file_content, filename, content_type)
        return url
    
    
    #add delete later
    


storage_service = StorageService()

