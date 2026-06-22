# backend/api/routes/blockchain.py
"""
Blockchain integration routes for WALLET-TRUST.

Handles token generation, verification, and blockchain interactions.
"""

import logging
import time
import re
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from web3 import Web3

from api.schemas import TokenValidationRequest, TokenGenerationRequest
from auth.jwt_handler import require_auth
from config import config
from core.blockchain import get_web3_manager
from core.token_auth_client import get_token_auth_client
from db_service import TokenService

blockchain_bp = Blueprint('blockchain', __name__)
logger = logging.getLogger(__name__)


@blockchain_bp.route('/health', methods=['GET'])
def blockchain_health():
    """
    Comprehensive blockchain health check endpoint.
    
    Validates:
    - Configuration is present (environment variables)
    - Web3 connection to RPC endpoint
    - Contract address is valid (checksum)
    - Account has balance for gas fees
    - No recent connection failures
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "connected": bool,
            "rpc_url": str,
            "contract_address": str,
            "chain": {
                "id": int,
                "name": str
            },
            "account": {
                "address": str,
                "balance_eth": float,
                "has_balance": bool
            },
            "latest_block": {
                "number": int,
                "hash": str,
                "timestamp": int
            },
            "checks": {
                "config_valid": bool,
                "rpc_connected": bool,
                "contract_valid": bool,
                "account_funded": bool
            },
            "warnings": [str],
            "errors": [str]
        }
    
    HTTP Status:
        - 200: Service is healthy or degraded
        - 503: Service is unhealthy (all critical checks failed)
    """
    try:
        warnings = []
        errors = []
        checks = {
            'config_valid': False,
            'rpc_connected': False,
            'contract_valid': False,
            'account_funded': False
        }
        
        # ============================================================
        # CHECK 1: Configuration validation
        # ============================================================
        rpc_url = getattr(config, 'BLOCKCHAIN_RPC_URL', None)
        contract_address = getattr(config, 'BLOCKCHAIN_CONTRACT_ADDRESS', None)
        private_key = getattr(config, 'BLOCKCHAIN_PRIVATE_KEY', None)
        
        if not rpc_url:
            errors.append('BLOCKCHAIN_RPC_URL environment variable not set')
        if not contract_address:
            errors.append('CONTRACT_ADDRESS environment variable not set')
        if not private_key:
            errors.append('PRIVATE_KEY environment variable not set')
        
        if not errors:
            checks['config_valid'] = True
        
        # If config is invalid, return early (unhealthy)
        if errors:
            logger.warning(f"Blockchain health check failed - config invalid: {errors}")
            return jsonify({
                'status': 'unhealthy',
                'connected': False,
                'checks': checks,
                'errors': errors,
                'warnings': warnings,
                'message': 'Blockchain service not configured'
            }), 503
        
        # ============================================================
        # CHECK 2: Get Web3Manager instance
        # ============================================================
        w3_manager = get_web3_manager(config)
        
        if w3_manager is None:
            errors.append('Failed to initialize Web3Manager')
            logger.warning("Web3Manager initialization failed")
            return jsonify({
                'status': 'unhealthy',
                'connected': False,
                'checks': checks,
                'errors': errors,
                'warnings': warnings,
                'message': 'Failed to initialize blockchain connection'
            }), 503
        
        # ============================================================
        # CHECK 3: RPC Connection
        # ============================================================
        try:
            if not w3_manager.w3.is_connected():
                errors.append(f'Unable to connect to RPC: {rpc_url}')
                logger.warning(f"RPC connection failed to {rpc_url}")
            else:
                checks['rpc_connected'] = True
        except Exception as e:
            errors.append(f'RPC connection error: {str(e)[:100]}')
            logger.error(f"RPC connection check failed: {e}")
        
        # ============================================================
        # CHECK 4: Contract Address validation
        # ============================================================
        try:
            if Web3.is_address(contract_address):
                w3_manager.contract_address = Web3.to_checksum_address(contract_address)
                checks['contract_valid'] = True
            else:
                errors.append(f'Invalid contract address format: {contract_address[:20]}...')
        except Exception as e:
            errors.append(f'Contract address validation error: {str(e)[:100]}')
        
        # ============================================================
        # CHECK 5: Account balance check
        # ============================================================
        try:
            if checks['rpc_connected']:
                balance_wei = w3_manager.w3.eth.get_balance(w3_manager.account_address)
                balance_eth = w3_manager.w3.from_wei(balance_wei, 'ether')
                
                # Warn if account has low balance (< 0.01 ETH)
                if float(balance_eth) < 0.01:
                    warnings.append(f'Account balance is low: {float(balance_eth):.4f} ETH')
                else:
                    checks['account_funded'] = True
            else:
                warnings.append('Skipped account balance check (RPC not connected)')
        except Exception as e:
            warnings.append(f'Could not check account balance: {str(e)[:100]}')
        
        # ============================================================
        # CHECK 6: Get latest block info
        # ============================================================
        block_number = None
        block_hash = None
        block_timestamp = None
        
        try:
            if checks['rpc_connected']:
                latest_block = w3_manager.w3.eth.get_block('latest')
                block_number = latest_block['number']
                block_hash = latest_block['hash'].hex()
                block_timestamp = latest_block['timestamp']
        except Exception as e:
            warnings.append(f'Could not fetch latest block: {str(e)[:100]}')
        
        # ============================================================
        # Determine overall status
        # ============================================================
        # Status: healthy if all checks pass
        # Status: degraded if some checks fail but service is running
        # Status: unhealthy if critical checks fail
        
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        
        if errors:
            status = 'unhealthy'
        elif warnings or passed_checks < total_checks:
            status = 'degraded'
        else:
            status = 'healthy'
        
        # ============================================================
        # Build response
        # ============================================================
        response = {
            'status': status,
            'connected': checks['rpc_connected'],
            'rpc_url': rpc_url[-30:] if rpc_url else None,  # Show last 30 chars (hide API keys)
            'contract_address': contract_address,
            'chain': {
                'id': config.BLOCKCHAIN_CHAIN_ID,
                'name': 'Sepolia Testnet'
            },
            'account': {
                'address': w3_manager.account_address if w3_manager else None,
                'balance_eth': float(w3_manager.w3.from_wei(
                    w3_manager.w3.eth.get_balance(w3_manager.account_address),
                    'ether'
                )) if checks['rpc_connected'] else None,
                'has_balance': checks['account_funded']
            },
            'latest_block': {
                'number': block_number,
                'hash': block_hash,
                'timestamp': block_timestamp
            } if block_number else None,
            'checks': checks,
            'warnings': warnings,
            'errors': errors
        }
        
        # Determine HTTP status code
        http_status = 200 if status in ['healthy', 'degraded'] else 503
        
        logger.info(
            f"Blockchain health check: {status} "
            f"(checks: {passed_checks}/{total_checks}, "
            f"warnings: {len(warnings)}, "
            f"errors: {len(errors)})"
        )
        
        return jsonify(response), http_status
        
    except Exception as e:
        logger.error(f"Blockchain health check exception: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'connected': False,
            'checks': checks,
            'errors': [f'Unexpected error: {str(e)[:100]}'],
            'warnings': warnings
        }), 503



@blockchain_bp.route('/token/generate', methods=['POST'])
@require_auth
def generate_token():
    """
    Generate a new token on the blockchain.
    
    This performs a real blockchain transaction using JWT authentication.
    
    Request body:
    {
        "government_id_number": "123456789",
        "document_data": "Base64 encoded document"  (optional)
    }
    
    Returns:
        - 201: Token generated successfully
        - 400: Validation error
        - 401: Unauthorized
        - 503: Blockchain connection failed
        - 500: Blockchain transaction failed
    """
    try:
        user_id = g.user_id
        user_email = g.user_email
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        try:
            req = TokenGenerationRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.errors()
            }), 400
        
        # Check if user already has an identity token in database
        existing_tokens = TokenService.get_tokens_by_user(user_id)
        if existing_tokens:
             return jsonify({
                 'success': False,
                 'error': 'User already has an active identity token',
                 'token_hash': existing_tokens[0].id
             }), 400

        # TokenAuth client (Sepolia, bytes32 tokenHash contract)
        try:
            token_client = get_token_auth_client(config)
        except Exception as e:
            print("EXCEPTION in get_token_auth_client:", repr(e))
            logger.error(f"TokenAuth client init failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Blockchain service unavailable',
                'details': str(e)[:300] or 'TokenAuth client initialization failed'
            }), 503
        
        # Create document hash from government ID and user data
        # Using Keccak256 hash (compatible with Solidity)
        hash_input = f"{user_id}:{user_email}:{req.government_id_number}"
        document_hash = Web3.keccak(text=hash_input).hex()
        
        logger.info(f"Generating token for user: {user_id}, email: {user_email}")
        
        # Call blockchain to generate token
        # The on-chain contract expects a string `dataHash`.
        # We pass the computed keccak hash hex for traceability.
        try:
            tx_result = token_client.generate_token(data_hash=document_hash)
        except Exception as e:
            msg = str(e)
            logger.error(f"Token generation failed (TokenAuthClient): {msg}")
            return jsonify({
                'success': False,
                'error': 'Transaction would revert (preflight)',
                'revert_reason': msg[:300]
            }), 500
        
        # TokenAuthClient returns tx_hash always; receipt fields may exist
        if tx_result.get('tx_hash'):
            logger.info(f"Token generated: TX={tx_result['tx_hash']}, TokenHash={tx_result.get('token_hash')}")

            # Persist token record so it can be listed via /api/users/tokens
            try:
                # For bytes32-tokenHash contract, we use token_hash as the primary marker.
                token_hash = tx_result.get('token_hash')
                token_id_str = f"tok_{int(time.time())}_{token_hash or 'hash'}"
                TokenService.create_token(
                    token_id_str=token_id_str,
                    user_id=user_id,
                    token_id=None,  # Integer ID not returned by this version of contract
                    document_hash=document_hash,
                    tx_hash=tx_result.get('tx_hash'),
                    block_number=tx_result.get('block_number')
                )
            except Exception as e:
                logger.warning(f"Failed to persist token record: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Token generated successfully on blockchain',
                'user_id': user_id,
                'token_id': None,
                'token_hash': tx_result.get('token_hash'),
                'tx_hash': tx_result['tx_hash'],
                'block_number': tx_result.get('block_number'),
                'gas_used': tx_result.get('gas_used'),
                'status': tx_result.get('status'),
                'etherscan_url': f"https://sepolia.etherscan.io/tx/{tx_result['tx_hash']}",
            }), 201
        
    except Exception as e:
        logger.error(f"Token generation error: {e}", exc_info=True)
        return jsonify({
            'error': 'Token generation failed',
            'details': str(e)[:100]
        }), 500


@blockchain_bp.route('/token/verify', methods=['POST'])
@require_auth
def verify_token():
    """
    Verify a token on the blockchain and log the validation attempt.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        try:
            req = TokenValidationRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.errors()
            }), 400
        
        company_id = g.user_id
        
        # Get Web3Manager
        w3_manager = get_web3_manager(config)
        if w3_manager is None or not w3_manager.connected:
            return jsonify({
                'error': 'Blockchain service unavailable'
            }), 503
        
        token_to_verify = (req.token or '').strip()
        
        if not (token_to_verify.startswith('0x') and len(token_to_verify) == 66):
            # Attempt to resolve from DB
            db_token = TokenService.get_token_by_id(token_to_verify)
            if not db_token:
                from models import Token
                db_token = Token.query.filter(
                    (Token.id.ilike(f"{token_to_verify}%")) | 
                    (Token.tx_hash.ilike(f"0x{token_to_verify}%")) |
                    (Token.tx_hash.ilike(f"{token_to_verify}%"))
                ).first()
            if db_token and db_token.id and db_token.id.startswith('0x') and len(db_token.id) == 66:
                token_to_verify = db_token.id
                
        if not (token_to_verify.startswith('0x') and len(token_to_verify) == 66):
             match = re.search(r'0x[a-fA-F0-9]{64}', token_to_verify)
             if match:
                 token_to_verify = match.group(0)

        if not (token_to_verify.startswith('0x') and len(token_to_verify) == 66):
            return jsonify({
                'valid': False,
                'error': 'Could not resolve token to a valid blockchain hash.',
                'token': req.token
            }), 400

        try:
            token_client = get_token_auth_client(config)
            info = token_client.verify_token_hash(token_to_verify)
            is_valid = bool(info.get('is_valid'))
            
            # Log validation to database
            import time
            import uuid
            from db_service import ValidationService
            val_id = f"val_{int(time.time())}_{token_to_verify[-8:]}_{uuid.uuid4().hex[:6]}"
            
            # Find original token's tx_hash if possible
            db_token = TokenService.get_token_by_id(token_to_verify)
            tx_hash = db_token.tx_hash if db_token else None
            
            ValidationService.create_validation(
                validation_id=val_id,
                company_id=company_id,
                token=token_to_verify,
                is_valid=is_valid,
                tx_hash=tx_hash
            )
            
            return jsonify({
                'valid': is_valid,
                'token_id': None,
                'token_hash': token_to_verify,
                'user_address': info.get('generator'),
                'created_at': info.get('generated_at'),
                'data_hash': info.get('data_hash'),
            }), 200
        except Exception as e:
            return jsonify({
                'valid': False,
                'error': f"On-chain verification failed: {str(e)[:200]}",
                'token_hash': token_to_verify,
            }), 500
        
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        return jsonify({
            'error': 'Token verification failed',
            'details': str(e)[:100]
        }), 500


@blockchain_bp.route('/token/<token_hash>', methods=['GET'])
def get_token_details(token_hash):
    """
    Get full details for a token from the blockchain.
    
    URL parameters:
        token_hash: The token hash to retrieve (bytes32 format)
    
    Returns:
        - 200: Token details
        - 400: Invalid token hash
        - 503: Blockchain connection failed
        - 500: Retrieval error
    """
    try:
        # Validate token_hash format (0x + 64 hex chars)
        th = (token_hash or '').strip()
        if not (th.startswith('0x') and len(th) == 66):
            return jsonify({
                'error': 'Invalid token hash format - must be a 66-character hex string starting with 0x'
            }), 400
        
        # Get Web3Manager
        w3_manager = get_web3_manager(config)
        if w3_manager is None:
            return jsonify({
                'error': 'Blockchain service unavailable'
            }), 503
        
        if not w3_manager.connected:
            return jsonify({
                'error': 'Blockchain service unavailable'
            }), 503
        
        logger.info(f"Token details request for hash: {th}")
        
        # Verify token first
        verification_result = w3_manager.verify_token(th)
        
        if verification_result['success'] and verification_result.get('is_valid'):
            return jsonify({
                'token_hash': th,
                'valid': True,
                'user_address': verification_result.get('user_address'),
                'document_hash': verification_result.get('document_hash'),
                'created_at': verification_result.get('created_at'),
                'status': verification_result.get('status')
            }), 200
        else:
            return jsonify({
                'error': 'Token not found or invalid'
            }), 404
        
    except Exception as e:
        logger.error(f"Token details retrieval error: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve token details',
            'details': str(e)
        }), 500


@blockchain_bp.route('/tx-status/<tx_hash>', methods=['GET'])
def get_transaction_status(tx_hash):
    """
    Get comprehensive transaction status and health information.
    
    Endpoint: GET /api/blockchain/tx-status/<tx_hash>
    
    Path Parameters:
        tx_hash: Transaction hash (0x optional)
    
    Query Parameters:
        v: Verbosity level
            - "basic": Just status
            - "details": Full transaction details
            - "full": Everything including verification
    
    Returns:
        {
            "success": true,
            "status": "mined",
            "transaction": {
                "hash": "0x...",
                "sender": "0x...",
                "recipient": "0x...",
                "value": "0",
                "gas_used": 95000,
                "block_number": 5150221,
                "confirmation_blocks": 12
            },
            "execution": {
                "success": true,
                "status_code": 1,
                "error_message": null
            },
            "cost": {
                "gas_used": 95000,
                "gas_price_gwei": "50",
                "transaction_fee_eth": "0.00475"
            },
            "verification": {
                "sender_is_configured": true,
                "contract_address_correct": true,
                "mined_confirmation": true
            }
        }
    
    HTTP Status:
        - 200: Transaction found (mined or pending)
        - 404: Transaction not found
        - 503: Blockchain connection failed
        - 500: Error retrieving transaction
    """
    try:
        # Normalize tx_hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        if not len(tx_hash) == 66:
            logger.warning(f"Invalid transaction hash format: {tx_hash}")
            return jsonify({
                'success': False,
                'error': 'Invalid transaction hash format (expected 66 chars with 0x prefix)'
            }), 400
        
        logger.info(f"Checking TX status: {tx_hash}")
        
        # Get verbosity level
        verbosity = request.args.get('v', 'details').lower()
        if verbosity not in ['basic', 'details', 'full']:
            verbosity = 'details'
        
        # Get Web3Manager
        w3_manager = get_web3_manager(config)
        if w3_manager is None:
            return jsonify({
                'success': False,
                'status': 'unavailable',
                'error': 'Blockchain service unavailable'
            }), 503
        
        if not w3_manager.connected:
            return jsonify({
                'success': False,
                'status': 'unavailable',
                'error': 'Blockchain service unavailable'
            }), 503
        
        # BASIC: Check if transaction exists
        try:
            tx = w3_manager.w3.eth.get_transaction(tx_hash)
            logger.info(f"✅ Transaction found: {tx_hash}")
        except Exception as e:
            logger.warning(f"❌ Transaction not found: {tx_hash}")
            return jsonify({
                'success': False,
                'status': 'not_found',
                'error': 'Transaction not found on blockchain'
            }), 404
        
        # Check receipt and confirmation
        try:
            receipt = w3_manager.w3.eth.get_transaction_receipt(tx_hash)
            is_mined = True
            logger.info(f"✅ Receipt found - transaction mined at block {receipt['blockNumber']}")
        except Exception as e:
            is_mined = False
            receipt = None
            logger.info(f"⏳ Transaction pending (not yet mined)")
        
        # Build basic response
        response = {
            'success': True,
            'status': 'mined' if is_mined else 'pending',
            'transaction': {
                'hash': tx['hash'].hex(),
                'sender': tx['from'],
                'recipient': tx['to'],
                'value': str(tx['value']),
                'value_eth': str(w3_manager.w3.from_wei(tx['value'], 'ether')),
                'gas_limit': tx['gas'],
                'gas_price_wei': str(tx['gasPrice']),
                'gas_price_gwei': str(w3_manager.w3.from_wei(tx['gasPrice'], 'gwei')),
            }
        }
        
        if is_mined and receipt:
            # Add mining details
            response['transaction'].update({
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber'],
                'block_hash': receipt['blockHash'].hex(),
                'transaction_index': receipt['transactionIndex'],
            })
            
            response['execution'] = {
                'success': receipt['status'] == 1,
                'status_code': receipt['status'],
                'error_message': None if receipt['status'] == 1 else 'Transaction reverted',
                'status_text': 'SUCCESS' if receipt['status'] == 1 else 'FAILED'
            }
            
            logger.info(f"{'✅' if receipt['status'] == 1 else '❌'} Transaction status: {response['execution']['status_text']}")
            
            # Calculate cost
            tx_fee_wei = receipt['gasUsed'] * tx['gasPrice']
            tx_fee_eth = w3_manager.w3.from_wei(tx_fee_wei, 'ether')
            
            response['cost'] = {
                'gas_used': receipt['gasUsed'],
                'gas_price_gwei': str(w3_manager.w3.from_wei(tx['gasPrice'], 'gwei')),
                'transaction_fee_wei': str(tx_fee_wei),
                'transaction_fee_eth': str(tx_fee_eth)
            }
            
            logger.info(f"💰 Transaction fee: {tx_fee_eth} ETH")
            
            # Get confirmations
            try:
                latest_block = w3_manager.w3.eth.get_block('latest')
                confirmations = latest_block['number'] - receipt['blockNumber']
                response['transaction']['confirmation_blocks'] = confirmations
                response['transaction']['confirmed'] = confirmations >= 12
                logger.info(f"🔗 Confirmations: {confirmations} blocks")
            except Exception as e:
                logger.warning(f"Could not get confirmation count: {e}")
            
            # Verification
            try:
                configured_address = config.BLOCKCHAIN_PRIVATE_KEY
                from eth_account import Account
                expected_sender = Account.from_key(configured_address).address
                contract_address = config.BLOCKCHAIN_CONTRACT_ADDRESS
                
                response['verification'] = {
                    'sender_is_configured': tx['from'].lower() == expected_sender.lower(),
                    'contract_address_correct': tx['to'].lower() == Web3.to_checksum_address(contract_address).lower(),
                    'mined_confirmation': is_mined,
                    'confirmed': confirmations >= 12 if 'confirmations' in locals() else False
                }
                
                if response['verification']['sender_is_configured']:
                    logger.info("✅ Sender address matches configured wallet")
                else:
                    logger.warning("⚠️ Sender address differs from configured wallet")
                
                if response['verification']['contract_address_correct']:
                    logger.info("✅ Recipient is correct contract address")
                else:
                    logger.warning("⚠️ Recipient differs from configured contract")
            
            except Exception as e:
                logger.warning(f"Could not perform verification: {e}")
                response['verification'] = {
                    'error': 'Could not verify'
                }
            
            if verbosity in ['details', 'full']:
                response['details'] = {
                    'nonce': tx['nonce'],
                    'transaction_index': receipt['transactionIndex'],
                    'cumulative_gas': receipt['cumulativeGasUsed'],
                    'logs_count': len(receipt['logs']),
                    'input_data': tx['input']
                }
        else:
            response['execution'] = {
                'success': None,
                'status_code': None,
                'error_message': 'Transaction still pending - not yet mined',
                'status_text': 'PENDING'
            }
            
            response['verification'] = {
                'sender_is_configured': None,
                'mined_confirmation': False,
                'message': 'Verification available after mining'
            }
        
        # Add Etherscan link
        response['etherscan_url'] = f"https://sepolia.etherscan.io/tx/{tx_hash}"
        
        logger.info(f"✅ Status check complete for {tx_hash}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"❌ Error checking TX status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@blockchain_bp.route('/transaction/<tx_hash>', methods=['GET'])
def get_transaction_status_legacy(tx_hash):
    """
    Legacy endpoint for transaction status. Redirects to new endpoint.
    
    Deprecated: Use /api/blockchain/tx-status/<tx_hash> instead
    """
    try:
        # Normalize tx_hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        if not len(tx_hash) == 66:
            return jsonify({
                'error': 'Invalid transaction hash format'
            }), 400
        
        # Get Web3Manager
        w3_manager = get_web3_manager(config)
        if w3_manager is None:
            return jsonify({
                'error': 'Blockchain service unavailable'
            }), 503
        
        if not w3_manager.connected:
            return jsonify({
                'error': 'Blockchain service unavailable'
            }), 503
        
        logger.info(f"Transaction status request (legacy): {tx_hash[:20]}...")
        
        # Query transaction status
        tx_status = w3_manager.get_transaction_status(tx_hash)
        
        if tx_status['success']:
            return jsonify({
                'tx_hash': tx_status['tx_hash'],
                'status': tx_status['status'],
                'from': tx_status.get('from'),
                'to': tx_status.get('to'),
                'block_number': tx_status.get('block_number'),
                'gas_used': tx_status.get('gas_used'),
                'etherscan_url': f"https://sepolia.etherscan.io/tx/{tx_status['tx_hash']}"
            }), 200
        else:
            return jsonify({
                'error': tx_status.get('error', 'Transaction not found')
            }), 404
        
    except Exception as e:
        logger.error(f"Transaction status error: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve transaction status',
            'details': str(e)[:100]
        }), 500


@blockchain_bp.route('/contract/info', methods=['GET'])
def get_contract_info():
    """
    Get information about the deployed smart contract.
    
    Returns:
        - 200: Contract information with address and links
        - 500: Error
    """
    try:
        # Get Web3Manager for network info
        w3_manager = get_web3_manager(config)
        
        contract_address = config.BLOCKCHAIN_CONTRACT_ADDRESS
        if not contract_address:
            return jsonify({
                'error': 'Contract address not configured'
            }), 500
        
        # Normalize address
        try:
            from web3 import Web3
            contract_address = Web3.to_checksum_address(contract_address)
        except Exception as e:
            logger.warning(f"Invalid contract address format: {e}")
            pass
        
        return jsonify({
            'address': contract_address,
            'network': 'Sepolia Testnet',
            'network_id': 11155111,
            'chain_id': config.BLOCKCHAIN_CHAIN_ID if hasattr(config, 'BLOCKCHAIN_CHAIN_ID') else 11155111,
            'etherscan_url': f"https://sepolia.etherscan.io/address/{contract_address}",
            'connected': w3_manager.connected if w3_manager else False
        }), 200
        
    except Exception as e:
        logger.error(f"Contract info error: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve contract information',
            'details': str(e)[:100]
        }), 500
