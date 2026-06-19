"""
FILEBASE INTEGRATION EXAMPLES
Example Flask routes and functions using FilebaseStorage module

This file demonstrates:
- Initializing Filebase storage
- Uploading files
- Downloading files
- Handling errors
- Integration with Flask request/response
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
import os
import mimetypes
import time
import hashlib

from core.storage import FilebaseStorage
from db_service import DocumentService

logger = logging.getLogger(__name__)

# Create blueprint for storage routes
storage_bp = Blueprint('storage', __name__)


# ============================================================================
# EXAMPLE 1: Simple File Upload
# ============================================================================

@storage_bp.route('/api/storage/upload', methods=['POST'])
def upload_file():
    """
    Upload a file to Filebase
    
    Request:
        - Method: POST
        - File: multipart/form-data (file field)
        - Optional: object_key (custom S3 key)
    
    Returns:
        {
            'success': True,
            'file_url': 'https://s3.filebase.com/bucket/filename.txt',
            'object_key': 'filename.txt',
            'size': 1024,
            'message': 'File uploaded successfully'
        }
    """
    
    # Validate file exists
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided in request'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    try:
        # Initialize storage
        storage = FilebaseStorage(current_app.config)
        
        # Get custom object key if provided
        object_key = request.form.get('object_key') or secure_filename(file.filename)
        
        # Upload file
        success, final_key, result = storage.upload_bytes(
            file_data=file.read(),
            object_key=object_key,
            content_type=file.content_type or 'application/octet-stream'
        )
        
        if success:
            return jsonify({
                'success': True,
                'file_url': result,  # result contains the URL
                'object_key': final_key,
                'size': len(file.read()),
                'message': 'File uploaded successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result  # result contains error message
            }), 500
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# EXAMPLE 2: Upload with Additional Metadata
# ============================================================================

@storage_bp.route('/api/storage/upload-document', methods=['POST'])
def upload_document():
    """
    Upload a document with metadata
    
    Request:
        {
            'file': (file),
            'document_type': 'invoice',
            'user_id': '123',
            'description': 'Monthly invoice'
        }
    """
    
    file = request.files.get('file')
    document_type = request.form.get('document_type', 'document')
    user_id = request.form.get('user_id', 'unknown')
    description = request.form.get('description', '')
    
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        storage = FilebaseStorage(current_app.config)

        file_data = file.read()
        file_size = len(file_data)
        file_hash_sha256 = hashlib.sha256(file_data).hexdigest()
        
        # Create organized object key
        object_key = f"documents/{document_type}/{user_id}/{secure_filename(file.filename)}"
        
        success, key, url = storage.upload_bytes(
            file_data=file_data,
            object_key=object_key,
            content_type=file.content_type or 'application/octet-stream'
        )
        
        if success:
            doc_id = f"doc_fb_{int(time.time())}_{file_hash_sha256[:8]}"

            DocumentService.create_document(
                doc_id=doc_id,
                user_id=user_id,
                filename=secure_filename(file.filename),
                file_path=None,
                file_hash=file_hash_sha256,
                file_size=file_size,
                mime_type=file.content_type or 'application/octet-stream',
                encrypted=True,
                metadata={
                    'storage_provider': 'filebase',
                    'file_url': url,
                    'object_key': key,
                    'document_type': document_type,
                    'description': description
                }
            )
            return jsonify({
                'success': True,
                'file_url': url,
                'object_key': key,
                'document_type': document_type,
                'metadata': {
                    'user_id': user_id,
                    'description': description
                }
            }), 201
        else:
            return jsonify({'error': url}), 500
    
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 3: Upload Local File (from disk)
# ============================================================================

@storage_bp.route('/api/storage/backup', methods=['POST'])
def backup_file():
    """
    Backup a file from local disk to Filebase
    
    Request:
        {
            'local_path': '/path/to/file.txt'
        }
    """
    
    data = request.get_json()
    local_path = data.get('local_path')
    
    if not local_path:
        return jsonify({'error': 'local_path required'}), 400
    
    try:
        storage = FilebaseStorage(current_app.config)
        
        # Upload from disk
        success, key, url = storage.upload_file(
            file_path=local_path,
            object_key=f"backups/{Path(local_path).name}"
        )
        
        if success:
            return jsonify({
                'success': True,
                'file_url': url,
                'object_key': key
            }), 201
        else:
            return jsonify({'error': url}), 500
    
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 4: Download File
# ============================================================================

@storage_bp.route('/api/storage/download/<path:object_key>', methods=['GET'])
def download_file(object_key):
    """
    Download file from Filebase
    
    URL:
        GET /api/storage/download/documents/invoice/123/file.pdf
    """
    
    try:
        storage = FilebaseStorage(current_app.config)
        
        # Create temporary file
        temp_path = f"/tmp/{secure_filename(object_key.split('/')[-1])}"
        
        success, message = storage.download_file(object_key, temp_path)
        
        if success:
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=Path(object_key).name,
                mimetype=mimetypes.guess_type(object_key)[0] or 'application/octet-stream'
            )
        else:
            return jsonify({'error': message}), 404
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 5: List Objects
# ============================================================================

@storage_bp.route('/api/storage/list', methods=['GET'])
def list_files():
    """
    List files in Filebase bucket
    
    Query Parameters:
        - prefix: Filter by path prefix (e.g., 'documents/')
    
    Returns:
        [
            {
                'key': 'documents/invoice/123/file.pdf',
                'size': 102400,
                'modified': '2026-02-28T10:30:00',
                'url': 'https://s3.filebase.com/bucket/...'
            }
        ]
    """
    
    prefix = request.args.get('prefix', '')
    
    try:
        storage = FilebaseStorage(current_app.config)
        
        success, objects, error = storage.list_objects(prefix=prefix)
        
        if success:
            return jsonify({
                'success': True,
                'count': len(objects),
                'prefix': prefix,
                'objects': objects
            }), 200
        else:
            return jsonify({'error': error}), 500
    
    except Exception as e:
        logger.error(f"List error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 6: Delete File
# ============================================================================

@storage_bp.route('/api/storage/delete/<path:object_key>', methods=['DELETE'])
def delete_file(object_key):
    """
    Delete file from Filebase
    
    URL:
        DELETE /api/storage/delete/documents/invoice/123/file.pdf
    """
    
    try:
        storage = FilebaseStorage(current_app.config)
        
        success, message = storage.delete_object(object_key)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({'error': message}), 500
    
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 7: Check Storage Health
# ============================================================================

@storage_bp.route('/api/storage/health', methods=['GET'])
def check_storage_health():
    """
    Check Filebase connectivity
    
    Returns:
        {
            'healthy': True,
            'status': 'Filebase storage is online',
            'endpoint': 'https://s3.filebase.com',
            'bucket': 'pii-auth'
        }
    """
    
    try:
        storage = FilebaseStorage(current_app.config)
        
        is_connected, message = storage.check_connectivity()
        
        return jsonify({
            'healthy': is_connected,
            'status': message,
            'endpoint': storage.endpoint_url,
            'bucket': storage.bucket
        }), 200 if is_connected else 503
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'healthy': False,
            'error': str(e)
        }), 503


# ============================================================================
# EXAMPLE 8: Encrypt and Upload
# ============================================================================

@storage_bp.route('/api/storage/upload-encrypted', methods=['POST'])
def upload_encrypted():
    """
    Upload encrypted content to Filebase
    
    Request:
        {
            'file': (file),
            'encryption_key': 'base64_encoded_key'
        }
    """
    
    file = request.files.get('file')
    
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        from core.crypto import encrypt_file
        
        # Read and encrypt file
        file_data = file.read()
        encryption_key = request.form.get('encryption_key') or current_app.config.get('ENCRYPTION_KEY')
        
        encrypted_data = encrypt_file(file_data, encryption_key)
        
        # Upload encrypted data
        storage = FilebaseStorage(current_app.config)
        object_key = f"encrypted/{secure_filename(file.filename)}.enc"
        
        success, key, url = storage.upload_bytes(
            file_data=encrypted_data,
            object_key=object_key,
            content_type='application/octet-stream'
        )
        
        if success:
            return jsonify({
                'success': True,
                'file_url': url,
                'object_key': key,
                'encrypted': True
            }), 201
        else:
            return jsonify({'error': url}), 500
    
    except Exception as e:
        logger.error(f"Encrypted upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_storage_instance():
    """Get a Filebase storage instance"""
    try:
        return FilebaseStorage(current_app.config)
    except Exception as e:
        logger.error(f"Failed to initialize storage: {str(e)}")
        raise


def ensure_bucket_exists():
    """Verify bucket exists before operations"""
    try:
        storage = FilebaseStorage(current_app.config)
        is_connected, message = storage.check_connectivity()
        
        if not is_connected:
            raise Exception(f"Bucket not accessible: {message}")
        
        return True
    except Exception as e:
        logger.error(f"Bucket verification failed: {str(e)}")
        raise


# ============================================================================
# REGISTRATION
# ============================================================================

# Register storage blueprint in app_factory.py:
# from api.routes.storage_examples import storage_bp
# app.register_blueprint(storage_bp)
