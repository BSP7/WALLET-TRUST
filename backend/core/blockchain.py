"""
Blockchain integration module for WALLET-TRUST.

Handles Web3 connection, contract interaction, and blockchain transactions.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, Web3ValidationError
from eth_account import Account

logger = logging.getLogger(__name__)


class Web3Manager:
    """Manages Web3 connection and blockchain interactions."""
    
    # TokenAuth contract ABI for interaction
    CONTRACT_ABI = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "disabler", "type": "address"},
                {"indexed": True, "internalType": "bytes32", "name": "tokenHash", "type": "bytes32"},
                {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
            ],
            "name": "TokenDisabled",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "generator", "type": "address"},
                {"indexed": True, "internalType": "bytes32", "name": "tokenHash", "type": "bytes32"},
                {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
                {"indexed": False, "internalType": "string", "name": "dataHash", "type": "string"}
            ],
            "name": "TokenGenerated",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "verifier", "type": "address"},
                {"indexed": True, "internalType": "bytes32", "name": "tokenHash", "type": "bytes32"},
                {"indexed": False, "internalType": "bool", "name": "isValid", "type": "bool"},
                {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
            ],
            "name": "TokenVerified",
            "type": "event"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "tokenHash", "type": "bytes32"}],
            "name": "disableToken",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "string", "name": "dataHash", "type": "string"}],
            "name": "generateToken",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "getTokenCount",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "tokenHash", "type": "bytes32"}],
            "name": "getTokenDetails",
            "outputs": [
                {"internalType": "bool", "name": "isValid", "type": "bool"},
                {"internalType": "address", "name": "generator", "type": "address"},
                {"internalType": "uint256", "name": "generatedAt", "type": "uint256"},
                {"internalType": "string", "name": "dataHash", "type": "string"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "hasActiveToken",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "tokenCount",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "name": "tokenRegistry",
            "outputs": [
                {"internalType": "address", "name": "generator", "type": "address"},
                {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                {"internalType": "bool", "name": "active", "type": "bool"},
                {"internalType": "string", "name": "dataHash", "type": "string"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "", "type": "address"}],
            "name": "userToken",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "tokenHash", "type": "bytes32"}],
            "name": "verifyToken",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self, 
                 rpc_url: str,
                 contract_address: str,
                 private_key: str,
                 chain_id: int = 11155111):
        """
        Initialize Web3Manager.
        
        Args:
            rpc_url: Ethereum RPC endpoint URL
            contract_address: Smart contract address
            private_key: Private key for transactions (0x prefixed)
            chain_id: Chain ID (default: 11155111 for Sepolia)
        """
        self.rpc_url = rpc_url
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.chain_id = chain_id
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Validate connection
        if not self.w3.is_connected():
            logger.warning(f"Failed to connect to RPC: {rpc_url}")
            self.connected = False
        else:
            logger.info(f"Connected to blockchain: {self.w3.eth.chain_id}")
            self.connected = True
        
        # Setup account
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        self.account = Account.from_key(private_key)
        self.account_address = self.account.address
        logger.info(f"Using account: {self.account_address}")
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.CONTRACT_ABI
        )
        
        logger.info(f"Contract initialized at: {self.contract_address}")
    
    def get_gas_price(self) -> int:
        """Get current gas price with 10% buffer."""
        try:
            base_price = self.w3.eth.gas_price
            return int(base_price * 1.1)  # 10% premium for priority
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return int(50 * 10**9)  # Default 50 Gwei fallback
    
    def estimate_gas(self, function_call) -> int:
        """
        Estimate gas for a contract function call.
        
        Args:
            function_call: Web3 contract function call object
            
        Returns:
            Estimated gas with 20% buffer
        """
        try:
            estimate = function_call.estimate_gas({
                'from': self.account_address,
                'nonce': self.w3.eth.get_transaction_count(self.account_address, 'pending')
            })
            return int(estimate * 1.2)  # 20% buffer
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default 300000")
            return 300000
    
    def generate_token(self,
                      document_hash: str,
                      nonce: Optional[int] = None) -> Dict:
        """
        Generate a token on the blockchain with comprehensive logging.
        
        Args:
            document_hash: Keccak256 hash of the document (0x prefixed hex string)
            nonce: Optional custom nonce
            
        Returns:
            Dictionary with transaction hash, token hash, and status
        """
        try:
            if not self.connected:
                logger.error("❌ Blockchain connection not available")
                return {
                    'success': False,
                    'error': 'Blockchain connection failed',
                    'token_hash': None,
                    'tx_hash': None
                }
            
            # ============================================================
            # STEP 1: VERIFY SENDER ADDRESS
            # ============================================================
            configured_address = self.account_address
            logger.info(f"📍 STEP 1: Verify Sender Address")
            logger.info(f"   Configured address: {configured_address}")
            
            if not Web3.is_address(configured_address):
                logger.error(f"❌ Invalid sender address: {configured_address}")
                return {'success': False, 'error': 'Invalid wallet address'}
            
            sender_address = Web3.to_checksum_address(configured_address)
            logger.info(f"   ✅ Address validated (checksum): {sender_address}")
            
            # Check balance
            balance = self.w3.eth.get_balance(sender_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"   💰 Wallet balance: {balance_eth} ETH")
            
            if balance == 0:
                logger.warning(f"   ⚠️ WARNING: Wallet has 0 balance at {sender_address}")
            
            logger.info(f"📄 Generating token for document hash: {document_hash}")
            
            # Get nonce
            if nonce is None:
                nonce = self.w3.eth.get_transaction_count(self.account_address, 'pending')
            logger.info(f"   Transaction nonce: {nonce}")
            
            # Prepare function call
            func_call = self.contract.functions.generateToken(
                document_hash
            )

            # ============================================================
            # STEP 1B: PRE-FLIGHT SIMULATION (eth_call)
            # ============================================================
            # This catches require()/revert() reasons before spending gas.
            try:
                func_call.call({'from': sender_address})
                logger.info("   ✅ Pre-flight simulation (eth_call) succeeded")
            except ContractLogicError as e:
                revert_reason = str(e)
                logger.error(f"❌ Pre-flight revert (ContractLogicError): {revert_reason}")
                return {
                    'success': False,
                    'error': 'Transaction would revert (preflight)',
                    'revert_reason': revert_reason[:300],
                    'token_id': None,
                    'tx_hash': None,
                    'status': 0,
                    'logs': []
                }
            except ValueError as e:
                payload = e.args[0] if (e.args and isinstance(e.args[0], dict)) else None
                message = None
                if payload:
                    message = payload.get('message')
                    data_msg = payload.get('data')
                    if isinstance(data_msg, dict) and data_msg.get('message'):
                        message = f"{message} | {data_msg.get('message')}"
                if not message:
                    message = str(e)

                logger.error(f"❌ Pre-flight revert (ValueError): {message}")
                return {
                    'success': False,
                    'error': 'Transaction would revert (preflight)',
                    'revert_reason': (message or '')[:300],
                    'token_id': None,
                    'tx_hash': None,
                    'status': 0,
                    'logs': []
                }
            
            # Estimate gas
            gas_estimate = self.estimate_gas(func_call)
            gas_price = self.get_gas_price()
            logger.info(f"   Gas estimate: {gas_estimate} units")
            logger.info(f"   Gas price: {self.w3.from_wei(gas_price, 'gwei')} Gwei")
            
            # Build transaction
            tx_dict = func_call.build_transaction({
                'nonce': nonce,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': self.chain_id,
                'from': sender_address
            })
            
            # ============================================================
            # STEP 2: SIGN & SEND TRANSACTION
            # ============================================================
            logger.info(f"🔐 STEP 2: Sign & Send Transaction")
            signed_tx = self.account.sign_transaction(tx_dict)
            
            try:
                raw_tx = getattr(signed_tx, 'raw_transaction', None)
                if raw_tx is None:
                    raw_tx = getattr(signed_tx, 'rawTransaction', None)

                if raw_tx is None:
                    raise AttributeError(
                        "SignedTransaction missing raw transaction bytes (expected 'raw_transaction' or 'rawTransaction')."
                    )

                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
                tx_hash_hex = tx_hash.hex()
                
                logger.info("=" * 70)
                logger.info("📤 TRANSACTION SENT")
                logger.info("=" * 70)
                logger.info(f"Transaction Hash: {tx_hash_hex}")
                logger.info(f"Sender Address:   {sender_address}")
                logger.info(f"Contract Address: {self.contract_address}")
                logger.info(f"Document Hash:    {document_hash}")
                logger.info("=" * 70)
                
            except ValueError as e:
                payload = e.args[0] if (e.args and isinstance(e.args[0], dict)) else None
                message = None
                if payload:
                    message = payload.get('message')
                if not message:
                    message = str(e)

                msg_lc = (message or '').lower()
                if 'already known' in msg_lc or 'known transaction' in msg_lc:
                    tx_hash = self.w3.keccak(raw_tx)
                    tx_hash_hex = tx_hash.hex()
                    logger.warning(
                        f"⚠️ RPC reports transaction already known; continuing with tx_hash={tx_hash_hex}")
                else:
                    if payload:
                        logger.error(
                            f"❌ RPC rejected transaction: code={payload.get('code')} message={payload.get('message')} data={payload.get('data')}",
                            exc_info=True,
                        )
                    else:
                        logger.error(f"❌ Failed to send transaction: {e}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"❌ Failed to send transaction: {e}", exc_info=True)
                raise
            
            # ============================================================
            # STEP 3: WAIT FOR RECEIPT & CONFIRM MINING
            # ============================================================
            logger.info(f"⏳ STEP 3: Wait for Transaction to be Mined")
            logger.info(f"   Timeout: 120 seconds (check every 2 seconds)")
            
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=120,  # 2 minutes timeout
                    poll_latency=2  # Check every 2 seconds
                )
            except Exception as e:
                logger.error(f"⏳ Transaction still pending after 120 seconds: {tx_hash_hex}", exc_info=True)
                return {
                    'success': None,
                    'tx_hash': tx_hash_hex,
                    'message': 'Transaction pending. Check status later.',
                    'token_hash': None
                }
            
            logger.info("=" * 70)
            logger.info("✅ TRANSACTION MINED")
            logger.info("=" * 70)
            logger.info(f"Transaction Hash:    {receipt['transactionHash'].hex()}")
            logger.info(f"Block Number:        {receipt['blockNumber']}")
            logger.info(f"Block Hash:          {receipt['blockHash'].hex()}")
            logger.info(f"Gas Used:            {receipt['gasUsed']} units")
            effective_gas_price = receipt.get('effectiveGasPrice')
            if effective_gas_price is None:
                try:
                    tx_obj_for_gas = self.w3.eth.get_transaction(tx_hash)
                    effective_gas_price = tx_obj_for_gas.get('gasPrice')
                except Exception:
                    effective_gas_price = None

            if effective_gas_price is not None:
                logger.info(f"Gas Price:           {self.w3.from_wei(effective_gas_price, 'gwei')} Gwei")
            else:
                logger.info("Gas Price:           (unavailable)")
            logger.info(f"Transaction Index:   {receipt['transactionIndex']}")
            logger.info(f"Cumulative Gas Used: {receipt['cumulativeGasUsed']}")
            logger.info("=" * 70)

            # Serialize logs for API responses (json-safe)
            receipt_logs = receipt.get('logs') or []
            serializable_logs = []
            try:
                for log_item in receipt_logs:
                    topics = []
                    for t in (log_item.get('topics') or []):
                        try:
                            topics.append(t.hex())
                        except Exception:
                            topics.append(str(t))

                    data_value = log_item.get('data')
                    try:
                        data_hex = data_value.hex() if hasattr(data_value, 'hex') else str(data_value)
                    except Exception:
                        data_hex = str(data_value)

                    serializable_logs.append({
                        'address': str(log_item.get('address')),
                        'topics': topics,
                        'data': data_hex,
                        'logIndex': log_item.get('logIndex'),
                    })
            except Exception:
                serializable_logs = []
            
            # ============================================================
            # STEP 4: VERIFY SENDER MATCHES CONFIGURED WALLET
            # ============================================================
            logger.info(f"🔍 STEP 4: Verify Sender Address")
            tx_obj = self.w3.eth.get_transaction(tx_hash_hex)
            actual_sender = tx_obj['from']
            
            logger.info(f"Expected Sender:  {sender_address}")
            logger.info(f"Actual Sender:    {actual_sender}")
            
            if actual_sender.lower() == sender_address.lower():
                logger.info("✅ Sender address VERIFIED")
            else:
                logger.error(f"❌ Sender address MISMATCH!")
                return {
                    'success': False,
                    'error': 'Sender address mismatch',
                    'tx_hash': tx_hash_hex,
                    'token_id': None
                }
            
            # ============================================================
            # STEP 3C: CHECK TRANSACTION STATUS
            # ============================================================
            if receipt['status'] == 1:
                logger.info("✅ TRANSACTION SUCCESSFUL (Status: 1)")
                
                # Extract token hash from logs if available
                token_hash = self._extract_token_hash_from_receipt(receipt)
                
                logger.info(f"Token Hash: {token_hash}")
                
                # ============================================================
                # STEP 5: VERIFY ON-CHAIN DATA MATCHES UPLOADED DOCUMENT
                # ============================================================
                logger.info(f"🔐 STEP 5: Verify On-Chain Data")
                if token_hash:
                    try:
                        token_info = self.contract.functions.getTokenDetails(token_hash).call()
                        is_valid, stored_user, stored_timestamp, stored_data_hash = token_info
                        
                        logger.info(f"Token Hash:         {token_hash}")
                        logger.info(f"Stored Address:     {stored_user}")
                        logger.info(f"Stored Hash:        {stored_data_hash}")
                        logger.info(f"Stored Timestamp:   {stored_timestamp}")
                        logger.info(f"Is Valid:           {is_valid}")
                        
                        # Verify hash matches (note: contract stores dataHash which is the document hash)
                        if stored_data_hash.lower() == document_hash.lower():
                            logger.info("✅ Document hash VERIFIED on-chain")
                        else:
                            logger.error(f"❌ Hash mismatch between uploaded ({document_hash}) and stored ({stored_data_hash})")
                        
                        if is_valid:
                            logger.info("✅ Token is marked as VALID in smart contract")
                    except Exception as e:
                        logger.warning(f"Could not verify on-chain data: {e}")
                
                return {
                    'success': True,
                    'tx_hash': tx_hash_hex,
                    'token_hash': token_hash,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'status': receipt.get('status'),
                    'logs': serializable_logs,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error("❌ TRANSACTION FAILED (Status: 0)")
                logger.error(f"   Possible reasons:")
                logger.error(f"   - Insufficient gas")
                logger.error(f"   - Contract revert")
                logger.error(f"   - Invalid input parameters")

                # Best-effort: attempt to reproduce revert reason via eth_call
                revert_reason = None
                try:
                    call_tx = {
                        'from': sender_address,
                        'to': tx_dict.get('to') or self.contract_address,
                        'data': tx_dict.get('data'),
                        'value': tx_dict.get('value', 0),
                    }
                    block_id = receipt.get('blockNumber')
                    if isinstance(block_id, int) and block_id > 0:
                        block_id = block_id - 1
                    else:
                        block_id = 'latest'
                    self.w3.eth.call(call_tx, block_identifier=block_id)
                except ContractLogicError as e:
                    revert_reason = str(e)
                except ValueError as e:
                    payload = e.args[0] if (e.args and isinstance(e.args[0], dict)) else None
                    if payload and payload.get('message'):
                        revert_reason = payload.get('message')
                    else:
                        revert_reason = str(e)
                except Exception:
                    revert_reason = None

                return {
                    'success': False,
                    'error': 'Transaction execution failed',
                    'tx_hash': tx_hash_hex,
                    'token_hash': None,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt.get('gasUsed'),
                    'status': receipt.get('status'),
                    'logs': serializable_logs,
                    'revert_reason': (revert_reason[:300] if isinstance(revert_reason, str) else None)
                }
        
        except ContractLogicError as e:
            logger.error(f"❌ Transaction failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Transaction failed: {str(e)[:100]}',
                'token_hash': None,
                'tx_hash': None
            }
        except Web3ValidationError as e:
            logger.error(f"❌ Web3 validation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Validation error: {str(e)[:100]}',
                'token_hash': None,
                'tx_hash': None
            }
        except Exception as e:
            logger.error(f"❌ Token generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Token generation failed: {str(e)[:100]}',
                'token_hash': None,
                'tx_hash': None
            }
    
    def verify_token(self, token_hash: str) -> Dict:
        """
        Verify a token on the blockchain.
        
        Args:
            token_hash: Token hash to verify (0x prefixed)
            
        Returns:
            Dictionary with verification result and token info
        """
        try:
            if not self.connected:
                return {
                    'success': False,
                    'error': 'Blockchain connection failed',
                    'is_valid': False
                }
            
            logger.info(f"Verifying token: {token_hash}")

            if not token_hash.startswith('0x'):
                token_hash = '0x' + token_hash
            
            token_hash_bytes = Web3.to_bytes(hexstr=token_hash)
            
            # Call verifyToken function
            is_valid = self.contract.functions.verifyToken(token_hash_bytes).call()
            
            if is_valid:
                # Get detailed token info: isValid, generator, generatedAt, dataHash
                token_info = self.contract.functions.getTokenDetails(token_hash_bytes).call()
                
                validity_status = token_info[0]
                user_address = token_info[1]
                timestamp = token_info[2]
                document_hash = token_info[3]
                
                logger.info(f"Token {token_hash} verified successfully")
                
                return {
                    'success': True,
                    'is_valid': True,
                    'token_id': None, # We don't have integer token IDs anymore
                    'token_hash': token_hash,
                    'user_address': user_address,
                    'document_hash': document_hash,
                    'created_at': timestamp,
                    'status': 'VALID' if validity_status else 'INVALID'
                }
            else:
                logger.warning(f"Token {token_hash} verification failed")
                return {
                    'success': True,
                    'is_valid': False,
                    'token_hash': token_hash,
                    'status': 'INVALID'
                }
        
        except Exception as e:
            logger.error(f"Token verification error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Token verification failed: {str(e)[:100]}',
                'is_valid': False
            }

    
    def verify_transaction_sender(self, tx_hash: str, expected_sender: str) -> bool:
        """
        Verify that a transaction was sent from the configured wallet address.
        
        Args:
            tx_hash: Transaction hash to verify
            expected_sender: Expected sender address (from .env PRIVATE_KEY)
        
        Returns:
            True if sender matches expected address, False otherwise
        """
        try:
            # Get transaction details
            tx = self.w3.eth.get_transaction(tx_hash)
            
            actual_sender = tx['from']
            expected_sender_checksum = Web3.to_checksum_address(expected_sender)
            
            logger.info("=" * 70)
            logger.info("🔍 SENDER ADDRESS VERIFICATION")
            logger.info("=" * 70)
            logger.info(f"Expected Sender:  {expected_sender_checksum}")
            logger.info(f"Actual Sender:    {actual_sender}")
            logger.info(f"Match: {actual_sender.lower() == expected_sender_checksum.lower()}")
            logger.info("=" * 70)
            
            if actual_sender.lower() == expected_sender_checksum.lower():
                logger.info("✅ Sender address VERIFIED")
                return True
            else:
                logger.error(f"❌ Sender address MISMATCH!")
                logger.error(f"   Transaction came from: {actual_sender}")
                logger.error(f"   Expected from:         {expected_sender_checksum}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error verifying sender: {e}", exc_info=True)
            return False
    
    def get_latest_block(self) -> Dict:
        """Get latest block information."""
        try:
            if not self.connected:
                return {'connected': False}
            
            block = self.w3.eth.get_block('latest')
            return {
                'connected': True,
                'block_number': block['number'],
                'block_hash': block['hash'].hex(),
                'timestamp': block['timestamp'],
                'gas_used': block['gasUsed'],
                'miner': block['miner']
            }
        except Exception as e:
            logger.error(f"Error getting latest block: {e}")
            return {'connected': False, 'error': str(e)}
    
    def get_transaction_status(self, tx_hash: str) -> Dict:
        """
        Get transaction status.
        
        Args:
            tx_hash: Transaction hash (0x prefixed)
            
        Returns:
            Dictionary with transaction status
        """
        try:
            if not self.connected:
                return {'success': False, 'error': 'Blockchain connection failed'}
            
            # Normalize tx_hash
            if not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            
            try:
                tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            except Exception:
                # Transaction not yet mined
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    return {
                        'success': True,
                        'tx_hash': tx_hash,
                        'status': 'PENDING',
                        'from': tx['from'],
                        'to': tx['to']
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Transaction not found: {str(e)[:100]}'
                    }
            
            # Transaction mined
            status = 'SUCCESS' if tx_receipt['status'] == 1 else 'FAILED'
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'status': status,
                'block_number': tx_receipt['blockNumber'],
                'gas_used': tx_receipt['gasUsed'],
                'from': tx_receipt['from'],
                'to': tx_receipt['to']
            }
        
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return {
                'success': False,
                'error': str(e)[:100]
            }
    
    def get_account_balance(self) -> Dict:
        """Get account balance."""
        try:
            if not self.connected:
                return {'connected': False}
            
            balance_wei = self.w3.eth.get_balance(self.account_address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return {
                'connected': True,
                'address': self.account_address,
                'balance_wei': balance_wei,
                'balance_eth': float(balance_eth),
                'nonce': self.w3.eth.get_transaction_count(self.account_address)
            }
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _extract_token_hash_from_receipt(self, receipt) -> Optional[str]:
        """
        Extract token hash from transaction receipt logs.
        
        Looks for TokenGenerated event.
        """
        try:
            # event TokenGenerated(address indexed generator, bytes32 indexed tokenHash, ...)
            rich_logs = self.contract.events.TokenGenerated().process_receipt(receipt)
            if rich_logs:
                token_hash = rich_logs[0]['args']['tokenHash']
                if isinstance(token_hash, bytes):
                    return "0x" + token_hash.hex()
                return str(token_hash)
            return None
        except Exception as e:
            logger.warning(f"Could not extract token hash from receipt: {e}")
            return None


# Global Web3Manager instance (lazy initialized)
_web3_manager: Optional[Web3Manager] = None


def get_web3_manager(config) -> Optional[Web3Manager]:
    """
    Get or create Web3Manager instance.
    
    Args:
        config: Configuration object with blockchain settings
        
    Returns:
        Web3Manager instance or None if configuration is missing
    """
    global _web3_manager
    
    if _web3_manager is not None:
        return _web3_manager
    
    # Check if all required config is present
    if not all([
        getattr(config, 'BLOCKCHAIN_RPC_URL', None),
        getattr(config, 'BLOCKCHAIN_CONTRACT_ADDRESS', None),
        getattr(config, 'BLOCKCHAIN_PRIVATE_KEY', None)
    ]):
        logger.warning("Blockchain configuration incomplete - Web3Manager not initialized")
        return None
    
    try:
        _web3_manager = Web3Manager(
            rpc_url=config.BLOCKCHAIN_RPC_URL,
            contract_address=config.BLOCKCHAIN_CONTRACT_ADDRESS,
            private_key=config.BLOCKCHAIN_PRIVATE_KEY,
            chain_id=getattr(config, 'BLOCKCHAIN_CHAIN_ID', 11155111)
        )
        return _web3_manager
    except Exception as e:
        logger.error(f"Failed to initialize Web3Manager: {e}")
        return None
