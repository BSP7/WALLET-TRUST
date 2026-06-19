"""backend/core/token_auth_client.py

TokenAuth (bytes32 tokenHash) helper client.

This module is intentionally small and production-safe:
- Never logs private keys
- Exposes explicit preflight (eth_call) to catch reverts early
- Reads on-chain token ownership (tokenRegistry.generator) before sending tx
- Builds/sends EIP-1559 transactions when possible

It is designed for the TokenAuth contract in:
- blockchain/contracts/Token_Auth.sol
ABI source:
- blockchain/contract_abi.json

"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union, cast

from eth_account import Account
from hexbytes import HexBytes
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from web3.types import TxParams

logger = logging.getLogger(__name__)

Bytes32Like = Union[str, bytes, bytearray, HexBytes]


def _mask_address(addr: str) -> str:
    if not addr or len(addr) < 10:
        return addr
    return f"{addr[:6]}…{addr[-4:]}"


def _normalize_private_key(private_key: str) -> str:
    if not private_key:
        raise ValueError("Missing private key")

    pk = private_key.strip()
    if pk.startswith("0x"):
        pk = pk[2:]

    if len(pk) != 64:
        raise ValueError(f"Invalid private key length: {len(pk)} (expected 64 hex chars)")

    # Accept hex string without 0x
    return pk


def _to_bytes32(value: Bytes32Like) -> HexBytes:
    """Convert a tokenHash to bytes32 (HexBytes length 32).

    Accepts:
    - 0x-prefixed hex string
    - raw 32-byte bytes-like
    """
    if isinstance(value, HexBytes):
        b = value
    elif isinstance(value, (bytes, bytearray)):
        b = HexBytes(bytes(value))
    elif isinstance(value, str):
        v = value.strip()
        if v.startswith("0x"):
            b = HexBytes(v)
        else:
            b = HexBytes("0x" + v)
    else:
        raise TypeError(f"Unsupported bytes32 value type: {type(value)}")

    if len(b) != 32:
        raise ValueError(f"Expected 32 bytes for bytes32, got {len(b)} bytes")

    return b


def extract_revert_reason(exc: Exception) -> str:
    """Best-effort revert reason extraction for web3.py v6.

    Nodes differ in how they return errors. We attempt:
    - ContractLogicError string message
    - ValueError dict payload with message/data
    """
    if isinstance(exc, ContractLogicError):
        msg = str(exc)
        return msg

    if isinstance(exc, ValueError) and exc.args:
        payload = exc.args[0]
        if isinstance(payload, dict):
            message = payload.get("message")
            data = payload.get("data")
            # Some providers return nested dict keyed by tx hash
            if isinstance(data, dict):
                nested_message = data.get("message")
                if nested_message:
                    if message:
                        return f"{message} | {nested_message}"
                    return nested_message
            if message:
                return message

    return str(exc)


def _load_tokenauth_abi() -> list[dict[str, Any]]:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    abi_path = os.path.join(repo_root, "blockchain", "contract_abi.json")

    with open(abi_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    abi = raw.get("abi") if isinstance(raw, dict) else None
    if not isinstance(abi, list):
        raise ValueError(f"Invalid ABI JSON at {abi_path}")

    return abi


def _fee_params(w3: Web3) -> Dict[str, int]:
    """Return EIP-1559 fee params when available, else legacy gasPrice."""
    try:
        pending_block = w3.eth.get_block("pending")
        base_fee = pending_block.get("baseFeePerGas")
        # web3.py v6 exposes a suggested tip
        tip = getattr(w3.eth, "max_priority_fee", None)
        if base_fee is not None and tip is not None:
            max_priority = int(tip)
            # conservative: 2x baseFee + tip
            max_fee = int(int(base_fee) * 2 + max_priority)
            return {"maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority}
    except Exception:
        pass

    gas_price = w3.eth.gas_price
    return {"gasPrice": int(int(gas_price) * 11 // 10)}


@dataclass(frozen=True)
class TokenRegistryEntry:
    generator: str
    timestamp: int
    active: bool
    data_hash: str


class TokenAuthClient:
    """Minimal client for TokenAuth contract."""

    def __init__(
        self,
        rpc_url: str,
        contract_address: str,
        private_key: str,
        chain_id: int = 11155111,
        abi: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id = int(chain_id)

        if not self.w3.is_connected():
            raise RuntimeError(f"Web3 not connected to RPC: {rpc_url}")

        checksum_address = Web3.to_checksum_address(contract_address)
        self.contract_address = checksum_address

        pk = _normalize_private_key(private_key)
        self.account = Account.from_key(pk)
        self.signer_address = Web3.to_checksum_address(self.account.address)

        if abi is None:
            abi = _load_tokenauth_abi()

        self.contract: Contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

        # Sanity check: ensure the target address actually speaks the TokenAuth ABI.
        # If the address points at a different contract (or a reverting fallback),
        # web3 often surfaces this as "execution reverted; no data".
        try:
            _ = self.contract.functions.tokenCount().call()
        except Exception as e:
            raise RuntimeError(
                "Contract interface check failed: tokenCount() reverted. "
                "The configured CONTRACT_ADDRESS likely does not match the TokenAuth ABI "
                "(wrong address or wrong network). "
                f"Details: {extract_revert_reason(e)}"
            ) from e

        logger.info(
            "TokenAuthClient ready | chain_id=%s | signer=%s | contract=%s",
            self.w3.eth.chain_id,
            _mask_address(self.signer_address),
            _mask_address(self.contract_address),
        )

    def get_backend_wallet_address(self) -> str:
        """Address derived from PRIVATE_KEY (safe to log)."""
        return self.signer_address

    def get_token_registry(self, token_hash: Bytes32Like) -> TokenRegistryEntry:
        h = _to_bytes32(token_hash)
        generator, timestamp, active, data_hash = self.contract.functions.tokenRegistry(h).call()
        return TokenRegistryEntry(
            generator=Web3.to_checksum_address(generator),
            timestamp=int(timestamp),
            active=bool(active),
            data_hash=str(data_hash),
        )

    def has_active_token(self, address: Optional[str] = None) -> bool:
        caller = Web3.to_checksum_address(address or self.signer_address)
        return bool(self.contract.functions.hasActiveToken().call({"from": caller}))

    def simulate_generate(self, data_hash: str, from_address: Optional[str] = None) -> None:
        caller = Web3.to_checksum_address(from_address or self.signer_address)
        self.contract.functions.generateToken(str(data_hash)).call({"from": caller})

    def generate_token(
        self,
        data_hash: str,
        *,
        wait_for_receipt: bool = True,
        timeout: int = 180,
    ) -> Dict[str, Any]:
        """Send generateToken(dataHash) transaction and return tx hash + emitted tokenHash."""

        # Preflight simulation (captures revert reasons before gas is spent)
        try:
            self.simulate_generate(data_hash, from_address=self.signer_address)
        except Exception as e:
            raise RuntimeError(f"generateToken would revert (preflight): {extract_revert_reason(e)}") from e

        fn = self.contract.functions.generateToken(str(data_hash))
        nonce = self.w3.eth.get_transaction_count(self.signer_address, "pending")
        fee = _fee_params(self.w3)

        try:
            gas_estimate = fn.estimate_gas({"from": self.signer_address})
            gas_limit = int(int(gas_estimate) * 12 // 10)
        except Exception:
            gas_limit = 300_000

        tx_params: TxParams = cast(
            TxParams,
            {
                "from": self.signer_address,
                "chainId": self.chain_id,
                "nonce": nonce,
                "gas": gas_limit,
                **fee,
            },
        )
        tx = fn.build_transaction(tx_params)

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

        result: Dict[str, Any] = {"tx_hash": tx_hash.hex()}

        if wait_for_receipt:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            result.update(
                {
                    "status": int(receipt.get("status", 0)),
                    "block_number": int(receipt.get("blockNumber")),
                    "gas_used": int(receipt.get("gasUsed")),
                }
            )

            # Extract emitted tokenHash from TokenGenerated event
            try:
                events = self.contract.events.TokenGenerated().process_receipt(receipt)
                if events:
                    args = events[0].get("args", {})
                    token_hash = args.get("tokenHash")
                    if token_hash is not None:
                        # tokenHash may be HexBytes
                        result["token_hash"] = HexBytes(token_hash).hex()
                    generator = args.get("generator")
                    if generator:
                        result["generator"] = Web3.to_checksum_address(generator)
            except Exception:
                # Don't fail the request if event parsing fails
                pass

        return result

    def verify_token_hash(self, token_hash: Bytes32Like) -> Dict[str, Any]:
        h = _to_bytes32(token_hash)
        is_valid = bool(self.contract.functions.verifyToken(h).call())
        valid, generator, generated_at, data_hash = self.contract.functions.getTokenDetails(h).call()
        return {
            "is_valid": bool(is_valid and valid),
            "generator": Web3.to_checksum_address(generator),
            "generated_at": int(generated_at),
            "data_hash": str(data_hash),
        }


_CLIENT: Optional[TokenAuthClient] = None


def get_token_auth_client(config: Any) -> TokenAuthClient:
    """Create (and cache) a TokenAuthClient from backend config."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    rpc_url = getattr(config, "BLOCKCHAIN_RPC_URL", None)
    contract_address = getattr(config, "BLOCKCHAIN_CONTRACT_ADDRESS", None)
    private_key = getattr(config, "BLOCKCHAIN_PRIVATE_KEY", None)
    chain_id = int(getattr(config, "BLOCKCHAIN_CHAIN_ID", 11155111))

    if not rpc_url or not contract_address or not private_key:
        raise RuntimeError("Blockchain config missing (BLOCKCHAIN_RPC_URL/CONTRACT_ADDRESS/PRIVATE_KEY)")

    _CLIENT = TokenAuthClient(
        rpc_url=rpc_url,
        contract_address=contract_address,
        private_key=private_key,
        chain_id=chain_id,
    )
    return _CLIENT
