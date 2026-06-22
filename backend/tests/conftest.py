import pytest
import os
from unittest.mock import patch, MagicMock

# Set test config before importing anything
os.environ['JWT_SECRET'] = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
os.environ['ENCRYPTION_KEY'] = 'gS5M8rGgXkXkZ8e4mZ_8Y4N_oW-V0ZcR1vQ5rDq7t_o='
os.environ['JWT_EXPIRATION_HOURS'] = '1'
os.environ['BLOCKCHAIN_RPC_URL'] = 'http://localhost:8545'
os.environ['CONTRACT_ADDRESS'] = '0x1234567890123456789012345678901234567890'
os.environ['PRIVATE_KEY'] = '0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['AUTO_CREATE_DATABASE'] = 'false'
os.environ['ARGON2_TIME_COST'] = '1'
os.environ['ARGON2_MEMORY_COST'] = '1024'

from app_factory import create_app
from models import db

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def mock_crypto_manager():
    # Real crypto manager handles the DB just fine, just use reduced argon settings via env
    yield None

@pytest.fixture
def mock_web3_manager():
    with patch('core.blockchain.Web3') as mock_web3:
        # Prevent Web3Manager from actually connecting, just pretend it did
        mock_web3.return_value.is_connected.return_value = True
        mock_web3.return_value.eth.chain_id = 11155111
        mock_web3.return_value.eth.get_transaction_count.return_value = 1
        yield mock_web3

@pytest.fixture
def mock_token_client():
    with patch('api.routes.blockchain.get_token_auth_client') as mock:
        instance = MagicMock()
        instance.generate_token_hash.return_value = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        instance.verify_token_hash.return_value = {
            'is_valid': True,
            'generator': '0xABC',
            'generated_at': 1234567890,
            'data_hash': '0xDEF'
        }
        instance.generate_token.return_value = {
            'status': 1,
            'tx_hash': '0xABC',
            'token_hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        }
        mock.return_value = instance
        
        # Also patch it for documents route
        with patch('api.routes.documents.get_token_auth_client') as doc_mock:
            doc_mock.return_value = instance
            yield instance

storage_mock_data = {}

@pytest.fixture
def mock_ipfs():
    with patch('api.routes.documents.storage') as mock:
        
        def fake_upload(*args, **kwargs):
            obj_key = kwargs.get('object_key') or (args[1] if len(args) > 1 else 'test_key')
            storage_mock_data[obj_key] = kwargs.get('file_data') or args[0]
            return True, obj_key, 'ipfs://QmTest123', 'QmTest123'
            
        def fake_download(key, dest_path):
            with open(dest_path, 'wb') as f:
                f.write(storage_mock_data.get(key, b"dummy fallback if empty"))
            return True, "success"
            
        mock.upload_bytes.side_effect = fake_upload
        mock.download_file.side_effect = fake_download
        yield mock
