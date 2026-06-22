import pytest
from unittest.mock import patch, MagicMock
from web3.exceptions import ContractLogicError
from core.blockchain import Web3Manager

@pytest.fixture
def valid_web3_config():
    return {
        'rpc_url': 'http://127.0.0.1:8545',
        'contract_address': '0x1234567890123456789012345678901234567890',
        'private_key': '0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
    }

@patch('core.blockchain.Web3')
def test_web3manager_initialization(mock_web3_class, valid_web3_config):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_web3_class.return_value = mock_w3
    mock_web3_class.to_checksum_address.return_value = valid_web3_config['contract_address']
    
    manager = Web3Manager(**valid_web3_config)
    assert manager.w3.is_connected() is True

@patch('core.blockchain.Web3')
def test_generate_token_success(mock_web3_class, valid_web3_config):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_web3_class.return_value = mock_w3
    mock_web3_class.to_checksum_address.side_effect = lambda x: x
    
    mock_account = MagicMock()
    mock_account.address = '0xSenderAddress'
    
    with patch('core.blockchain.Account.from_key', return_value=mock_account):
        manager = Web3Manager(**valid_web3_config)
        
        mock_func = MagicMock()
        mock_func.build_transaction.return_value = {'gas': 200000, 'gasPrice': 1000000000, 'nonce': 1}
        manager.contract.functions.generateToken.return_value = mock_func
        
        mock_w3.eth.get_transaction_count.return_value = 1
        
        mock_signed_tx = MagicMock()
        mock_signed_tx.rawTransaction = b'signed_tx_bytes'
        
        mock_w3.eth.account.sign_transaction.return_value = mock_signed_tx
        mock_w3.eth.send_raw_transaction.return_value = b'tx_hash'
        
        mock_w3.eth.get_transaction.return_value = {'from': '0xSenderAddress', 'to': '0x1234567890123456789012345678901234567890'}
        mock_receipt = {'status': 1, 'logs': [], 'transactionHash': b'tx_hash', 'blockNumber': 1, 'blockHash': b'block_hash', 'gasUsed': 21000, 'transactionIndex': 0, 'cumulativeGasUsed': 21000}
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        
        mock_event = {'args': {'tokenHash': b'token_hash_bytes'}}
        manager.contract.events.TokenGenerated().process_receipt.return_value = [mock_event]
        
        # Override the estimate_gas properly to avoid hitting real web3 node
        with patch.object(manager, 'estimate_gas', return_value=300000):
            with patch.object(manager, 'get_gas_price', return_value=1000000000):
                res = manager.generate_token('data_hash_123')
                
                assert res.get('success') is True
                assert res.get('tx_hash') == b'tx_hash'.hex()
                assert res.get('token_hash') == '0x' + b'token_hash_bytes'.hex()

@patch('core.blockchain.Web3')
def test_generate_token_revert(mock_web3_class, valid_web3_config):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_web3_class.return_value = mock_w3
    
    with patch('core.blockchain.Account.from_key'):
        manager = Web3Manager(**valid_web3_config)
        
        manager.contract.functions.generateToken.side_effect = ContractLogicError("execution reverted")
        
        res = manager.generate_token('data_hash_123')
        assert res.get('success') is False
        assert "execution reverted" in res.get('error', '')

@patch('core.blockchain.Web3')
def test_verify_token_valid(mock_web3_class, valid_web3_config):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_web3_class.return_value = mock_w3
    
    with patch('core.blockchain.Account.from_key'):
        manager = Web3Manager(**valid_web3_config)
        
        mock_func = MagicMock()
        mock_func.call.return_value = [True, '0xGen', 1234567890, 'data_hash', True]
        manager.contract.functions.getTokenDetails.return_value = mock_func
        manager.contract.functions.verifyToken.return_value = mock_func
        
        # Let's mock call return for getTokenDetails
        mock_func2 = MagicMock()
        mock_func2.call.return_value = [True, '0xGen', 1234567890, 'data_hash', True]
        manager.contract.functions.getTokenDetails.return_value = mock_func2

        res = manager.verify_token('0xValidTokenHash')
        # Check actual format it returns
        assert isinstance(res, dict)
