import pytest
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from core.storage import FilebaseStorage

@pytest.fixture
def storage_config():
    return {
        'FILEBASE_ENDPOINT': 'https://s3.filebase.com',
        'FILEBASE_BUCKET': 'test-bucket',
        'FILEBASE_ACCESS_KEY': 'test-access',
        'FILEBASE_SECRET_KEY': 'test-secret',
        'FILEBASE_TIMEOUT': 10,
        'FILEBASE_MAX_RETRIES': 1
    }

@patch('core.storage.boto3.client')
def test_storage_initialization(mock_boto3, storage_config):
    storage = FilebaseStorage(storage_config)
    mock_boto3.assert_called_once()
    assert storage.bucket == 'test-bucket'

def test_storage_initialization_missing_keys():
    with pytest.raises(ValueError):
        FilebaseStorage({'FILEBASE_BUCKET': 'test'})

@patch('core.storage.boto3.client')
def test_upload_bytes_success(mock_boto3, storage_config):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    # Setup head_object to return CID metadata
    mock_client.head_object.return_value = {
        'Metadata': {'cid': 'QmTestCID123'}
    }
    mock_client.put_object.return_value = {'ETag': '"mock-etag"'}
    
    storage = FilebaseStorage(storage_config)
    
    success, key, url, cid = storage.upload_bytes(b"data", "test.txt")
    assert success is True
    assert key == "test.txt"
    assert url == "https://s3.filebase.com/test-bucket/test.txt"
    assert cid == "QmTestCID123"
    
    mock_client.put_object.assert_called_once_with(
        Bucket='test-bucket', 
        Key='test.txt', 
        Body=b"data", 
        ContentType='application/octet-stream'
    )

@patch('core.storage.boto3.client')
def test_upload_bytes_etag_fallback(mock_boto3, storage_config):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    # Missing cid in Metadata, but ETag provided
    mock_client.head_object.return_value = {'Metadata': {}}
    mock_client.put_object.return_value = {'ETag': '"QmFallbackCID"'}
    
    storage = FilebaseStorage(storage_config)
    
    success, key, url, cid = storage.upload_bytes(b"data", "test2.txt")
    assert success is True
    assert cid == "QmFallbackCID"

@patch('core.storage.boto3.client')
def test_upload_bytes_client_error(mock_boto3, storage_config):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
    mock_client.put_object.side_effect = ClientError(error_response, 'PutObject')
    
    storage = FilebaseStorage(storage_config)
    
    success, key, url, cid = storage.upload_bytes(b"data", "test3.txt")
    assert success is False
    assert "S3 Error (AccessDenied)" in url
    assert cid is None

@patch('core.storage.boto3.client')
def test_download_file_success(mock_boto3, storage_config, tmpdir):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    storage = FilebaseStorage(storage_config)
    out_path = os.path.join(tmpdir, "out.txt")
    
    success, msg = storage.download_file("test.txt", out_path)
    assert success is True
    mock_client.download_file.assert_called_once_with('test-bucket', 'test.txt', out_path)

@patch('core.storage.boto3.client')
def test_check_connectivity_success(mock_boto3, storage_config):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    storage = FilebaseStorage(storage_config)
    
    success, msg = storage.check_connectivity()
    assert success is True
    mock_client.head_bucket.assert_called_once_with(Bucket='test-bucket')

@patch('core.storage.boto3.client')
def test_check_connectivity_failure(mock_boto3, storage_config):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    error_response = {'Error': {'Code': '404', 'Message': 'Not Found'}}
    mock_client.head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
    
    storage = FilebaseStorage(storage_config)
    
    success, msg = storage.check_connectivity()
    assert success is False
    assert "Bucket not found" in msg
