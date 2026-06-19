"""
Filebase Storage Operations Module
Handles all S3-compatible upload/download operations with error handling
"""

import os
import logging
import mimetypes
from typing import Optional, Dict, Tuple

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)


class FilebaseStorage:
    """Manages Filebase S3-compatible storage operations"""
    
    def __init__(self, config: Dict):
        """Initialize storage client"""
        self.endpoint_url = config.get('FILEBASE_ENDPOINT', 'https://s3.filebase.com')
        self.bucket = config.get('FILEBASE_BUCKET')
        self.access_key = config.get('FILEBASE_ACCESS_KEY')
        self.secret_key = config.get('FILEBASE_SECRET_KEY')
        self.timeout = int(config.get('FILEBASE_TIMEOUT', 30))
        self.max_retries = int(config.get('FILEBASE_MAX_RETRIES', 3))
        
        if not all([self.access_key, self.secret_key, self.bucket]):
            raise ValueError("Missing required Filebase configuration")
        
        self.client = self._create_client()
    
    def _create_client(self):
        """Create S3 client"""
        try:
            client_config = Config(
                connect_timeout=self.timeout,
                read_timeout=self.timeout,
                retries={'max_attempts': self.max_retries}
            )
            
            return boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='us-east-1',
                config=client_config
            )
        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise
    
    def upload_file(self, file_path: str, object_key: Optional[str] = None, content_type: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Upload file to Filebase"""
        try:
            if not os.path.exists(file_path):
                return False, "", f"File not found: {file_path}"
            
            object_key = object_key or os.path.basename(file_path)
            content_type = content_type or mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            with open(file_path, 'rb') as f:
                self.client.put_object(Bucket=self.bucket, Key=object_key, Body=f.read(), ContentType=content_type)
            
            file_url = f"{self.endpoint_url}/{self.bucket}/{object_key}"
            logger.info(f"File uploaded: {file_url}")
            return True, object_key, file_url
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Upload failed: {error_code}")
            return False, "", f"S3 Error ({error_code})"
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return False, "", str(e)
    
    def upload_bytes(self, file_data: bytes, object_key: str, content_type: str = 'application/octet-stream') -> Tuple[bool, str, Optional[str]]:
        """Upload bytes to Filebase"""
        try:
            self.client.put_object(Bucket=self.bucket, Key=object_key, Body=file_data, ContentType=content_type)
            file_url = f"{self.endpoint_url}/{self.bucket}/{object_key}"
            logger.info(f"Bytes uploaded: {file_url}")
            return True, object_key, file_url
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Upload failed: {error_code}")
            return False, "", f"S3 Error ({error_code})"
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return False, "", str(e)
    
    def download_file(self, object_key: str, output_path: str) -> Tuple[bool, str]:
        """Download file from Filebase"""
        try:
            self.client.download_file(self.bucket, object_key, output_path)
            logger.info(f"File downloaded: {output_path}")
            return True, "Download successful"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Download failed: {error_code}")
            return False, f"S3 Error: {error_code}"
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return False, str(e)
    
    def check_connectivity(self) -> Tuple[bool, str]:
        """Check Filebase connectivity"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            msg = f"Connected to Filebase bucket '{self.bucket}' successfully"
            logger.info(msg)
            return True, msg
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                msg = f"Bucket not found: {self.bucket}"
            elif error_code == '403':
                msg = "Invalid credentials or access denied"
            else:
                msg = f"Client error: {error_code}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Connection failed: {str(e)}"
            logger.error(msg)
            return False, msg
    
    def list_objects(self, prefix: str = '') -> Tuple[bool, list, Optional[str]]:
        """List objects in bucket"""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({'key': obj['Key'], 'size': obj['Size'], 'url': f"{self.endpoint_url}/{self.bucket}/{obj['Key']}"})
            return True, objects, None
        except Exception as e:
            logger.error(f"List error: {str(e)}")
            return False, [], str(e)
    
    def delete_object(self, object_key: str) -> Tuple[bool, str]:
        """Delete object from Filebase"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            logger.info(f"Object deleted: {object_key}")
            return True, f"Object deleted: {object_key}"
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            return False, str(e)
    
    def get_file_url(self, object_key: str) -> str:
        """Get public URL for a file"""
        return f"{self.endpoint_url}/{self.bucket}/{object_key}"
