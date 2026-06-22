#!/usr/bin/env python3
"""
Blockchain Diagnostics Tool for WALLET TRUST
==================================================

This script checks if your blockchain setup is correct and helps diagnose
why token generation or blockchain transactions might be failing.

Run this before reporting issues with blockchain functionality.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{END}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{END}")

def print_error(text):
    print(f"{RED}❌ {text}{END}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{END}")

def print_info(text):
    print(f"ℹ️  {text}")

def check_environment_variables():
    """Check if all required environment variables are set."""
    print_header("1. CHECKING ENVIRONMENT VARIABLES")
    
    required_vars = {
        'ALCHEMY_API_KEY': 'Alchemy API key for Ethereum connection',
        'SEPOLIA_RPC_URL': 'Sepolia RPC URL',
        'PRIVATE_KEY': 'Backend account private key',
        'CONTRACT_ADDRESS': 'Deployed smart contract address'
    }
    
    all_valid = True
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive data
            if 'KEY' in var_name:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
            else:
                masked = value
            print_success(f"{var_name}: {masked}")
        else:
            print_error(f"{var_name}: NOT SET - {description}")
            all_valid = False
    
    return all_valid

def check_web3_connection():
    """Check if Web3 can connect to Ethereum."""
    print_header("2. CHECKING WEB3 CONNECTION")
    
    try:
        from web3 import Web3, HTTPProvider
        print_success("Web3 library imported successfully")
        
        rpc_url = os.getenv('SEPOLIA_RPC_URL')
        if not rpc_url:
            print_error("SEPOLIA_RPC_URL not set in .env")
            return False
        
        print_info(f"Connecting to: {rpc_url[:50]}...")
        web3 = Web3(HTTPProvider(rpc_url))
        
        if web3.is_connected():
            print_success("✓ Connected to Ethereum network")
            
            # Check network info
            chain_id = web3.eth.chain_id
            block_number = web3.eth.block_number
            
            print_success(f"Chain ID: {chain_id} (Sepolia)")
            print_success(f"Latest block: {block_number}")
            
            return web3
        else:
            print_error("Could not connect to Ethereum network")
            print_error("Check SEPOLIA_RPC_URL in .env file")
            return None
            
    except ImportError:
        print_error("Web3 library not installed: pip install web3")
        return None
    except Exception as e:
        print_error(f"Web3 connection error: {str(e)}")
        return None

def check_account():
    """Check if backend account is properly configured."""
    print_header("3. CHECKING BACKEND ACCOUNT")
    
    try:
        from web3 import Web3
        
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print_error("PRIVATE_KEY not set in .env")
            return None
        
        # Validate private key format
        if not private_key.startswith('0x'):
            print_warning("Private key should start with '0x'")
            private_key = '0x' + private_key
        
        if len(private_key) != 66:
            print_error(f"Invalid private key length: {len(private_key)} (expected 66)")
            return None
        
        print_success("Private key format is valid")
        
        # Derive account from private key
        web3 = Web3()
        account = web3.eth.account.from_key(private_key)
        
        print_success(f"Account address: {account.address}")
        print_info(f"Use this address to fund account with ETH from faucet:")
        print_info(f"https://sepoliafaucet.com/")
        
        return account
        
    except Exception as e:
        print_error(f"Account verification error: {str(e)}")
        return None

def check_account_balance(web3, account):
    """Check ETH balance of backend account."""
    print_header("4. CHECKING ACCOUNT BALANCE")
    
    try:
        if not web3 or not account:
            print_warning("Cannot check balance - Web3 or account not available")
            return False
        
        balance_wei = web3.eth.get_balance(account.address)
        balance_eth = web3.from_wei(balance_wei, 'ether')
        
        if balance_eth == 0:
            print_error(f"Account balance: 0 ETH")
            print_error("Add ETH from faucet: https://sepoliafaucet.com/")
            return False
        
        print_success(f"Account balance: {balance_eth:.6f} ETH")
        
        # Estimate gas cost
        gas_price = web3.eth.gas_price
        gas_price_gwei = web3.from_wei(gas_price, 'gwei')
        estimated_cost = web3.from_wei(gas_price * 100000, 'ether')  # 100k gas
        
        print_info(f"Current gas price: {gas_price_gwei:.2f} gwei")
        print_info(f"Estimated cost per token: ~{estimated_cost:.6f} ETH")
        
        if balance_eth < estimated_cost * 10:
            print_warning(f"Low balance! Add more ETH to generate multiple tokens")
        
        return True
        
    except Exception as e:
        print_error(f"Balance check error: {str(e)}")
        return False

def check_contract_deployment(web3, account):
    """Check if smart contract is deployed at the specified address."""
    print_header("5. CHECKING CONTRACT DEPLOYMENT")
    
    try:
        contract_address = os.getenv('CONTRACT_ADDRESS')
        if not contract_address:
            print_error("CONTRACT_ADDRESS not set in .env")
            return False
        
        # Validate address format
        if not contract_address.startswith('0x'):
            print_error(f"Invalid contract address: {contract_address}")
            return False
        
        # Convert to checksum address
        checksum_address = web3.to_checksum_address(contract_address)
        print_success(f"Contract address: {checksum_address}")
        
        # Check if contract code exists
        code = web3.eth.get_code(checksum_address)
        
        if code == b'' or code == '0x':
            print_error(f"No contract code at {checksum_address}")
            print_error("Solution: Deploy contract first with:")
            print_error("  cd blockchain")
            print_error("  npx hardhat run scripts/deploy.js --network sepolia")
            return False
        
        print_success(f"Contract deployed (code size: {len(code)} bytes)")
        
        # Load and check ABI
        try:
            abi_path = os.path.join(BASE_DIR, "../blockchain/artifacts/contracts/Token_Auth.sol/TokenAuth.json")
            with open(abi_path, "r") as f:
                contract_json = json.load(f)
                abi = contract_json["abi"]
            print_success(f"Contract ABI loaded ({len(abi)} functions/events)")
        except Exception as e:
            print_warning(f"Could not load ABI: {e}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Contract check error: {str(e)}")
        return False

def check_owner_verification(web3, account):
    """Verify that backend account is the contract owner."""
    print_header("6. CHECKING CONTRACT OWNER")
    
    try:
        from web3 import Web3
        
        contract_address = os.getenv('CONTRACT_ADDRESS')
        if not contract_address:
            print_error("CONTRACT_ADDRESS not set")
            return False
        
        checksum_address = web3.to_checksum_address(contract_address)
        
        # Load ABI
        abi_path = os.path.join(BASE_DIR, "../blockchain/artifacts/contracts/Token_Auth.sol/TokenAuth.json")
        with open(abi_path, "r") as f:
            contract_json = json.load(f)
            abi = contract_json["abi"]
        
        contract = web3.eth.contract(address=checksum_address, abi=abi)
        
        print_info("Calling contract.owner()...")
        owner_address = contract.functions.owner().call()
        
        print_success(f"Contract owner: {owner_address}")
        print_info(f"Backend account: {account.address}")
        
        if owner_address.lower() == account.address.lower():
            print_success("✓ Backend account IS the contract owner")
            return True
        else:
            print_error("❌ Backend account is NOT the contract owner!")
            print_error("This is why blockchain transactions are failing!")
            print_error("")
            print_error("SOLUTION 1: Redeploy contract with current private key")
            print_error("  1. Copy current PRIVATE_KEY from .env")
            print_error("  2. cd blockchain")
            print_error("  3. Update .env with same PRIVATE_KEY")
            print_error("  4. npx hardhat run scripts/deploy.js --network sepolia")
            print_error("")
            print_error("SOLUTION 2: Update .env with correct private key")
            print_error("  1. Get private key that deployed the contract")
            print_error("  2. Update PRIVATE_KEY in backend/.env")
            print_error("  3. Ensure same key is in blockchain/.env")
            print_error("  4. Restart backend")
            return False
        
    except Exception as e:
        print_error(f"Owner verification error: {str(e)}")
        print_warning("Cannot verify owner - contract may be inaccessible")
        return False

def run_diagnostics():
    """Run all diagnostic checks."""
    print(f"\n{BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  BLOCKCHAIN DIAGNOSTICS FOR WALLET TRUST                   ║")
    print("║  This tool checks your blockchain configuration            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{END}")
    
    # Run checks
    env_valid = check_environment_variables()
    web3 = check_web3_connection()
    account = check_account()
    
    if web3 and account:
        check_account_balance(web3, account)
        contract_ok = check_contract_deployment(web3, account)
        
        if contract_ok:
            check_owner_verification(web3, account)
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    if env_valid and web3 and account:
        print_success("All checks passed! Your blockchain setup should work.")
        print_info("")
        print_info("Next steps:")
        print_info("1. Restart the backend server")
        print_info("2. Try generating a new token")
        print_info("3. Check backend logs for transaction details")
        print_info("4. Look up transaction on Etherscan:")
        print_info("   https://sepolia.etherscan.io/")
    else:
        print_error("Some checks failed. See above for details.")
        print_info("")
        print_info("Common issues:")
        print_info("1. Environment variables not set - update backend/.env")
        print_info("2. Web3 connection failed - check SEPOLIA_RPC_URL")
        print_info("3. Account balance is 0 - add ETH from faucet")
        print_info("4. Account is not contract owner - redeploy contract")
    
    print_header("")

if __name__ == "__main__":
    run_diagnostics()
