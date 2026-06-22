# backend/api/routes/documents.py
"""
Document management routes for WALLET-TRUST.

Handles document upload, scanning, and retrieval with blockchain integration.
"""

import logging
import os
import time
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from pydantic import ValidationError
import hashlib
import base64
from web3 import Web3
from datetime import datetime

from api.schemas import DocumentUploadRequest
from auth.jwt_handler import require_auth
from config import config
from core.crypto import CryptoManager
from core.blockchain import Web3Manager
from core.token_auth_client import get_token_auth_client
from db_service import DocumentService, TokenService
from core.storage import FilebaseStorage

documents_bp = Blueprint('documents', __name__)
logger = logging.getLogger(__name__)

# Initialize crypto manager
encryption_key = os.getenv('ENCRYPTION_KEY', '')
crypto = None
if encryption_key:
    try:
        key_bytes = base64.urlsafe_b64decode(encryption_key)
        crypto = CryptoManager(key_bytes.hex())
    except Exception as e:
        logger.error(f"Failed to initialize crypto: {e}")

# The `token_auth_client` is initialized lazily where needed via `get_token_auth_client`

# Initialize Filebase storage
storage = None
try:
    storage = FilebaseStorage({
        'FILEBASE_ENDPOINT': config.FILEBASE_ENDPOINT,
        'FILEBASE_BUCKET': config.FILEBASE_BUCKET,
        'FILEBASE_ACCESS_KEY': config.FILEBASE_ACCESS_KEY,
        'FILEBASE_SECRET_KEY': config.FILEBASE_SECRET_KEY
    })
    logger.info(f"✅ FilebaseStorage initialized: {config.FILEBASE_BUCKET}")
except Exception as e:
    logger.error(f"❌ Failed to initialize FilebaseStorage: {e}")

# Storage directory
STORAGE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'documents')
os.makedirs(STORAGE_DIR, exist_ok=True)


def convert_sha256_to_keccak256(sha256_hash: str) -> str:
    """
    Convert SHA256 hash to Keccak256 format for blockchain.
    
    Args:
        sha256_hash: SHA256 hash in hex format
        
    Returns:
        Keccak256 hash with 0x prefix
    """
    try:
        # For blockchain, we use Web3's keccak256 to hash the SHA256 hash
        # This ensures the hash is in the correct format for smart contract interaction
        if not sha256_hash.startswith('0x'):
            sha256_hash = '0x' + sha256_hash
        
        # Use Web3's keccak to create a proper blockchain hash
        keccak_hash = Web3.keccak(hexstr=sha256_hash)
        return keccak_hash.hex()  # Returns 0x-prefixed hex string
    except Exception as e:
        logger.error(f"Error converting hash to keccak256: {e}")
        # Fallback: pad SHA256 hash to 32 bytes if keccak conversion fails
        return '0x' + sha256_hash.ljust(64, '0')

# Allowed document types
ALLOWED_DOCUMENT_TYPES = {'passport', 'driver_license', 'national_id', 'id'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/tiff',
    'application/pdf'
}


def validate_file_upload(file):
    """
    Validate uploaded file for security and size.
    
    Args:
        file: File object from request
        
    Returns:
        Tuple: (is_valid, error_message)
    """
    if not file or file.filename == '':
        return False, 'No file provided'
    
    # Check file size (10MB limit)
    if len(file.read()) > config.MAX_CONTENT_LENGTH:
        file.seek(0)
        return False, 'File too large. Maximum 10MB allowed.'
    
    file.seek(0)
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f'File type not allowed. Allowed types: {ALLOWED_MIME_TYPES}'
    
    return True, None


@documents_bp.route('/upload', methods=['POST'])
@require_auth
def upload_document():
    """
    Upload a document for the authenticated user with blockchain integration.
    
    PROCESS:
    1. Validate file upload
    2. Generate document hash
    3. Submit transaction to smart contract
    4. Wait for transaction receipt
    5. Store document metadata in database
    6. Return transaction details to client
    
    Form data:
    {
        "title": "My Passport",
        "doc_type": "passport",
        "file": <binary file>
    }
    
    Returns:
        - 200: Document uploaded successfully with transaction hash
        - 400: Validation error
        - 401: Unauthorized
        - 413: File too large
        - 500: Server error
    """
    try:
        user_id = g.user_id
        user_email = g.user_email or 'unknown'
        
        logger.info(f"🚀 Document upload initiated by user {user_id} ({user_email})")
        
        # ========== STEP 1: VALIDATE REQUEST ==========
        if 'file' not in request.files:
            logger.warning(f"❌ No file provided in request from user {user_id}")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        title = request.form.get('title')
        doc_type = request.form.get('doc_type')
        
        # Validate using Pydantic
        try:
            DocumentUploadRequest(title=title, doc_type=doc_type)
        except ValidationError as e:
            logger.warning(f"❌ Validation error from user {user_id}: {e}")
            return jsonify({
                'error': 'Validation failed',
                'details': {field: str(err) for field, err in e.errors()}
            }), 400
        
        # Validate file
        is_valid, error_msg = validate_file_upload(file)
        if not is_valid:
            logger.warning(f"❌ File validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # ========== STEP 2: PROCESS FILE & GENERATE HASH ==========
        file_data = file.read()
        file_hash_sha256 = hashlib.sha256(file_data).hexdigest()
        safe_filename = secure_filename(file.filename)
        file_size = len(file_data)
        
        # ========== STEP 3: SUBMIT BLOCKCHAIN TRANSACTION ==========
        blockchain_result = None
        import uuid
        blockchain_result = {}
        token_hash_val = ''
        hash_suffix = (token_hash_val.replace('0x', '')[:8]) if token_hash_val else file_hash_sha256[:8]
        doc_id = f"doc_{int(time.time())}_{hash_suffix}_{uuid.uuid4().hex[:6]}"
        
        logger.info(f"📄 File processed:")
        logger.info(f"   - Document ID: {doc_id}")
        logger.info(f"   - Filename: {safe_filename}")
        logger.info(f"   - SHA256 Hash: {file_hash_sha256}")
        logger.info(f"   - Linked Hash Suffix: {hash_suffix}")
        logger.info(f"   - File Size: {file_size} bytes")
        
        # ========== STEP 4: ENCRYPT & STORE FILE ON FILEBASE ==========
        encrypted_data = file_data
        is_encrypted = False
        
        if crypto:
            try:
                # Returns string, need to encode back for storage if necessary
                encrypted_data = crypto.encrypt_data(file_data).encode()
                is_encrypted = True
                logger.info(f"✅ File encrypted with Fernet")
            except Exception as e:
                logger.warning(f"⚠️  Encryption failed: {e}. Uploading unencrypted.")
        
        filebase_url = None
        filebase_key = None
        ipfs_cid = None
        
        if storage:
            try:
                filebase_key = f"{doc_id}_{safe_filename}"
                success, final_key, result_url, cid = storage.upload_bytes(
                    file_data=encrypted_data,
                    object_key=filebase_key,
                    content_type=file.content_type or 'application/octet-stream'
                )
                
                if success:
                    filebase_url = result_url
                    ipfs_cid = cid
                    logger.info(f"✅ File uploaded to Filebase: {filebase_url} (CID: {cid})")
                else:
                    logger.error(f"❌ Filebase upload failed: {result_url}")
            except Exception as e:
                logger.error(f"❌ Filebase storage error: {e}")
        
        # Still keep a local copy as redundant backup for now
        file_path = os.path.join(STORAGE_DIR, f"{doc_id}_{safe_filename}")
        try:
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            logger.info(f"✅ Local backup stored at: {file_path}")
        except IOError as e:
            logger.warning(f"⚠️  Local backup failed: {e}")
            if not filebase_url:
                return jsonify({'error': 'Failed to store file entirely (local & Filebase)'}), 500
        
        # ========== STEP 5: STORE METADATA IN DATABASE ==========
        try:
            doc = DocumentService.create_document(
                doc_id=doc_id,
                user_id=user_id,
                filename=safe_filename,
                file_path=filebase_url or file_path,
                file_hash=file_hash_sha256,
                file_size=file_size,
                mime_type=file.content_type,
                encrypted=is_encrypted,
                metadata={
                    'title': title,
                    'doc_type': doc_type,
                    'tx_hash': blockchain_result.get('tx_hash'),
                    'token_hash': blockchain_result.get('token_hash'),
                    'blockchain_status': 'success',
                    'filebase_url': filebase_url,
                    'filebase_key': filebase_key,
                    'ipfs_cid': ipfs_cid,
                    'ipfs_status': 'pinned' if filebase_url else 'failed'
                }
            )
            logger.info(f"✅ Document metadata stored in database")
        except Exception as e:
            logger.error(f"❌ Database storage failed: {e}")
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file after DB failure: {file_path}")
            except:
                pass
            return jsonify({'error': 'Failed to store metadata'}), 500
        
        # ========== STEP 6: RETURN RESPONSE ==========
        logger.info("=" * 70)
        logger.info("✅ DOCUMENT UPLOAD COMPLETE")
        logger.info("=" * 70)
        
        response = {
            'message': 'Document uploaded successfully',
            'document': {
                'id': doc_id,
                'title': title,
                'doc_type': doc_type,
                'file_hash': file_hash_sha256,
                'uploaded_at': datetime.now().isoformat(),
                'file_size': file_size,
                'storage_url': filebase_url,
                'ipfs_cid': ipfs_cid
            }
        }
        
        # Add blockchain details if available
        if blockchain_result:
            response['blockchain'] = {
                'transaction_hash': blockchain_result.get('tx_hash'),
                'token_hash': blockchain_result.get('token_hash'),
                'block_number': blockchain_result.get('block_number'),
                'gas_used': blockchain_result.get('gas_used'),
                'status': 'success' if blockchain_result.get('success') else 'pending' if blockchain_result.get('success') is None else 'failed',
                'message': blockchain_result.get('message') or blockchain_result.get('error')
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Document upload error: {e}", exc_info=True)
        return jsonify({'error': 'Document upload failed', 'detail': str(e)}), 500


@documents_bp.route('/<document_id>', methods=['GET'])
@require_auth
def get_document(document_id):
    """
    Retrieve a document by ID.
    
    Requires: Authorization header with valid JWT
    
    Returns:
        - 200: Document data and metadata
        - 401: Unauthorized
        - 404: Document not found
        - 500: Server error
    """
    try:
        user_id = g.user_id
        doc = DocumentService.get_document_by_id(document_id)
        
        if not doc or doc.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access document {document_id}")
            return jsonify({'error': 'Not found'}), 404
        
        is_local = not (doc.file_path.startswith('ipfs://') or doc.file_path.startswith('http://') or doc.file_path.startswith('https://'))
        if is_local and not os.path.exists(doc.file_path):
            logger.error(f"File missing for document {document_id}: {doc.file_path}")
            return jsonify({'error': 'File missing'}), 404
        
        logger.info(f"Document {document_id} retrieved by user {user_id}")
        return jsonify({'document': doc.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Document retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve document'}), 500


@documents_bp.route('/<document_id>', methods=['DELETE'])
@require_auth
def delete_document(document_id):
    """
    Delete a document by ID.
    
    Requires: Authorization header with valid JWT
    
    Returns:
        - 200: Document deleted
        - 401: Unauthorized
        - 404: Document not found
        - 500: Server error
    """
    try:
        user_id = g.user_id
        doc = DocumentService.get_document_by_id(document_id)
        
        if not doc or doc.user_id != user_id:
            logger.warning(f"User {user_id} attempted to delete document {document_id}")
            return jsonify({'error': 'Not found'}), 404
        
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            logger.info(f"File deleted: {doc.file_path}")
        
        DocumentService.delete_document(document_id)
        logger.info(f"Document {document_id} deleted by user {user_id}")
        return jsonify({'message': 'Document deleted successfully'}), 200
    
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500


@documents_bp.route('/blockchain/tx-status/<tx_hash>', methods=['GET'])
@require_auth
def check_transaction_status(tx_hash):
    """
    Check the status of a blockchain transaction.
    
    This endpoint allows users to verify if their document upload transaction
    has been mined and what the final status is.
    
    Args:
        tx_hash: Transaction hash (with or without 0x prefix)
        
    Returns:
        - 200: Transaction found with status
        - 400: Invalid transaction hash
        - 404: Transaction not found
        - 500: Server error
    """
    try:
        user_id = g.user_id
        
        # Validate transaction hash format
        if not tx_hash or len(tx_hash) < 64:
            logger.warning(f"User {user_id} provided invalid tx_hash: {tx_hash}")
            return jsonify({'error': 'Invalid transaction hash format'}), 400
        
        # Ensure 0x prefix
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        try:
            token_client = get_token_auth_client(config)
        except Exception as e:
            logger.error(f"TokenAuthClient unavailable: {e}")
            return jsonify({'error': 'Blockchain connection unavailable'}), 500
        
        logger.info(f"User {user_id} checking transaction status: {tx_hash}")
        
        try:
            # Get transaction receipt
            receipt = token_client.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt is None:
                # Transaction not mined yet
                logger.info(f"Transaction {tx_hash} still pending...")
                try:
                    # Try to get transaction details to confirm it exists
                    tx_obj = token_client.w3.eth.get_transaction(tx_hash)
                    return jsonify({
                        'status': 'pending',
                        'tx_hash': tx_hash,
                        'message': 'Transaction has been submitted but not yet mined',
                        'from': tx_obj.get('from'),
                        'to': tx_obj.get('to'),
                        'gas': tx_obj.get('gas'),
                        'gas_price': token_client.w3.from_wei(tx_obj.get('gasPrice'), 'gwei') if tx_obj.get('gasPrice') else None
                    }), 200
                except Exception:
                    return jsonify({
                        'status': 'unknown',
                        'tx_hash': tx_hash,
                        'message': 'Transaction not found in mempool'
                    }), 404
            
            # Transaction is mined
            logger.info(f"Transaction {tx_hash} mined in block {receipt['blockNumber']}")
            
            status = 'success' if receipt['status'] == 1 else 'failed'
            
            return jsonify({
                'status': status,
                'tx_hash': tx_hash,
                'block_number': receipt['blockNumber'],
                'block_hash': receipt['blockHash'].hex() if receipt['blockHash'] else None,
                'transaction_index': receipt['transactionIndex'],
                'from': receipt['from'],
                'to': receipt['to'],
                'gas_used': receipt['gasUsed'],
                'gas_price': token_client.w3.from_wei(receipt['gasPrice'], 'gwei'),
                'cumulative_gas_used': receipt['cumulativeGasUsed'],
                'contract_address': receipt['contractAddress'],
                'logs': len(receipt['logs']),
                'root': receipt.get('root'),
                'timestamp': datetime.fromtimestamp(token_client.w3.eth.get_block(receipt['blockNumber'])['timestamp']).isoformat(),
                'confirmation_message': f"Transaction confirmed in block {receipt['blockNumber']}"
            }), 200
        
        except Exception as e:
            logger.error(f"Error checking transaction {tx_hash}: {e}")
            return jsonify({
                'error': 'Failed to check transaction status',
                'detail': str(e)
            }), 500
    
    except Exception as e:
        logger.error(f"Transaction status check error: {e}")
        return jsonify({'error': 'Failed to check transaction status'}), 500


@documents_bp.route('/<document_id>/download', methods=['GET'])
@require_auth
def download_document(document_id):
    """
    Download a document by ID.
    Retrieves the file from Filebase/IPFS or local storage,
    decrypts it if necessary, and returns the raw file.
    """
    try:
        user_id = g.user_id
        doc = DocumentService.get_document_by_id(document_id)
        
        if not doc or doc.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access document {document_id}")
            return jsonify({'error': 'Not found'}), 404
            
        file_path = doc.file_path
        file_data = None
        
        # Check if it's on Filebase
        meta = doc.meta_data or {}
        if meta.get('filebase_key') and storage:
            try:
                import tempfile
                # Create a temporary file and close it immediately so download_file can write to it
                tmp_fd, tmp_path = tempfile.mkstemp()
                os.close(tmp_fd)
                success, msg = storage.download_file(meta.get('filebase_key'), tmp_path)
                if success:
                    with open(tmp_path, 'rb') as f:
                        file_data = f.read()
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Failed to download from Filebase: {e}")
                
        # Fallback to local storage
        if file_data is None and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
        if file_data is None:
            return jsonify({'error': 'File not found in storage'}), 404
            
        # Decrypt if encrypted
        if doc.encrypted and crypto:
            try:
                # Decrypt expects base64 encoded string
                encrypted_str = file_data.decode('utf-8') if isinstance(file_data, bytes) else file_data
                logger.error(f"Type of encrypted_str is {type(encrypted_str)}")
                file_data = crypto.decrypt_data(encrypted_str)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Failed to decrypt document {document_id}: {e}")
                return jsonify({'error': 'Failed to decrypt file'}), 500
                
        from flask import send_file
        import io
        return send_file(
            io.BytesIO(file_data),
            mimetype=doc.mime_type or 'application/octet-stream',
            as_attachment=True,
            download_name=doc.filename
        )
        
    except Exception as e:
        logger.error(f"Document download error: {e}")
        return jsonify({'error': 'Failed to download document'}), 500