#!/usr/bin/env python3
"""
FILEBASE CONNECTIVITY TEST SCRIPT
Tests Filebase S3-compatible API using boto3

Usage:
    python filebase_test.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

import boto3
from botocore.exceptions import ClientError, ConnectionError, BotoCoreError
from botocore.vendored.requests.packages.urllib3.exceptions import ConnectTimeoutError


class FilebaseConnector:
    """Test Filebase connectivity using boto3"""
    
    def __init__(self):
        """Initialize Filebase S3 client"""
        self.access_key = os.getenv('FILEBASE_ACCESS_KEY')
        self.secret_key = os.getenv('FILEBASE_SECRET_KEY')
        self.endpoint_url = os.getenv('ENDPOINT_URL', 'https://s3.filebase.com')
        self.bucket_name = os.getenv('BUCKET_NAME')
        self.client = None
    
    def validate_credentials(self):
        """Validate that all required credentials are present"""
        logger.info("=" * 60)
        logger.info("STEP 1: Validating Credentials")
        logger.info("=" * 60)
        
        checks = {
            'Access Key': self.access_key,
            'Secret Key': self.secret_key,
            'Endpoint URL': self.endpoint_url,
            'Bucket Name': self.bucket_name
        }
        
        all_valid = True
        for name, value in checks.items():
            if value:
                # Mask sensitive values
                if 'Key' in name or 'Secret' in name:
                    display = value[:6] + '****' if len(value) > 6 else '****'
                else:
                    display = value
                logger.info(f"  ✅ {name}: {display}")
            else:
                logger.error(f"  ❌ {name}: NOT SET")
                all_valid = False
        
        return all_valid
    
    def connect(self):
        """Establish connection to Filebase"""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Connecting to Filebase")
        logger.info("=" * 60)
        
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='us-east-1'
            )
            logger.info("  ✅ Connected to Filebase successfully")
            return True
        except Exception as e:
            logger.error(f"  ❌ Connection failed: {str(e)}")
            return False
    
    def list_buckets(self):
        """List all available buckets"""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: Listing Available Buckets")
        logger.info("=" * 60)
        
        if not self.client:
            logger.error("  ❌ Not connected. Call connect() first")
            return False
        
        try:
            response = self.client.list_buckets()
            buckets = response.get('Buckets', [])
            
            if buckets:
                logger.info(f"  ✅ Found {len(buckets)} bucket(s):")
                for bucket in buckets:
                    logger.info(f"    - {bucket['Name']} (Created: {bucket['CreationDate']})")
                
                # Check if target bucket exists
                bucket_names = [b['Name'] for b in buckets]
                if self.bucket_name in bucket_names:
                    logger.info(f"  ✅ Target bucket '{self.bucket_name}' found")
                    return True
                else:
                    logger.warning(f"  ⚠️  Target bucket '{self.bucket_name}' NOT found")
                    return False
            else:
                logger.warning("  ⚠️  No buckets found")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidAccessKeyId':
                logger.error(f"  ❌ Invalid Access Key ID")
            elif error_code == 'SignatureDoesNotMatch':
                logger.error(f"  ❌ Invalid Secret Key (signature mismatch)")
            else:
                logger.error(f"  ❌ Client Error: {error_code}")
            return False
        except ConnectionError as e:
            logger.error(f"  ❌ Connection Error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Timeout: {str(e)}")
    
    def test_authentication(self):
        """Test authentication by attempting a simple operation"""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: Testing Authentication")
        logger.info("=" * 60)
        
        if not self.client:
            logger.error("  ❌ Not connected. Call connect() first")
            return False
        
        try:
            # Try to access bucket metadata
            response = self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"  ✅ Authentication successful")
            logger.info(f"  ✅ Bucket '{self.bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"  ❌ Bucket not found: {self.bucket_name}")
            elif error_code == '403':
                logger.error(f"  ❌ Access Denied - Check credentials")
            else:
                logger.error(f"  ❌ Client Error ({error_code})")
            return False
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
            return False
    
    def test_upload(self, file_path: Optional[str] = None, test_content: Optional[str] = None):
        """Test file upload to Filebase"""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Testing File Upload")
        logger.info("=" * 60)
        
        if not self.client:
            logger.error("  ❌ Not connected. Call connect() first")
            return False
        
        # Use provided file or create test content
        if file_path and Path(file_path).exists():
            test_key = Path(file_path).name
            with open(file_path, 'rb') as f:
                file_data = f.read()
            logger.info(f"  Uploading file: {test_key}")
        else:
            test_key = 'filebase-test.txt'
            file_data = (test_content or 'Filebase connectivity test').encode()
            logger.info(f"  Uploading test content: {test_key}")
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=file_data
            )
            logger.info(f"  ✅ File uploaded successfully: {test_key}")
            
            # Try to retrieve the file URL
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{test_key}"
            logger.info(f"  📍 File URL: {file_url}")
            
            return True
        except ClientError as e:
            logger.error(f"  ❌ Upload failed: {e.response['Error']['Code']}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Upload error: {str(e)}")
            return False
    
    def run_full_test(self):
        """Run complete diagnostic test"""
        logger.info("\n")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 10 + "FILEBASE CONNECTIVITY DIAGNOSTIC TEST" + " " * 10 + "║")
        logger.info("╚" + "=" * 58 + "╝")
        
        results = {
            'validation': self.validate_credentials(),
            'connection': self.connect(),
            'buckets': self.list_buckets() if self.client else False,
            'authentication': self.test_authentication() if self.client else False,
            'upload': self.test_upload() if self.client else False,
        }
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} - {test_name.capitalize()}")
        
        logger.info(f"\nResult: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("\n🎉 FILEBASE INTEGRATION IS WORKING CORRECTLY! 🎉")
            return True
        else:
            logger.error("\n⚠️  SOME TESTS FAILED - SEE ERRORS ABOVE")
            return False


def main():
    """Run the diagnostic test"""
    connector = FilebaseConnector()
    success = connector.run_full_test()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
