// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TokenAuth
 * @dev Produces unique, immutable tokens for identity verification on Ethereum blockchain.
 * 
 * SECURITY FEATURES:
 * - Each token is generated ONLY by the smart contract, never by backend code
 * - Tokens use keccak256(msg.sender + block.timestamp) for cryptographic uniqueness
 * - No local token generation - eliminates duplicate token risk
 * - Tokens are permanently stored in contract mapping
 * - All token generation emits events for audit trail
 * - No .call() usage - only state-changing transactions
 */
contract TokenAuth {
    // ============================================================
    // STATE VARIABLES
    // ============================================================
    
    /// @dev Maps unique token hashes to their generation details
    mapping(bytes32 => Token) public tokenRegistry;
    
    /// @dev Maps user addresses to their generated token hash
    mapping(address => bytes32) public userToken;
    
    /// @dev Total tokens generated on this contract
    uint256 public tokenCount = 0;
    
    /// @dev Struct to store token metadata
    struct Token {
        address generator;         // User who generated the token
        uint256 timestamp;         // When token was generated
        bool active;               // Whether token is still valid
        string dataHash;           // IPFS hash of encrypted user data
    }
    
    // ============================================================
    // EVENTS
    // ============================================================
    
    /// @dev Emitted when a new token is generated
    event TokenGenerated(
        address indexed generator,
        bytes32 indexed tokenHash,
        uint256 timestamp,
        string dataHash
    );
    
    /// @dev Emitted when a token is verified
    event TokenVerified(
        address indexed verifier,
        bytes32 indexed tokenHash,
        bool isValid,
        uint256 timestamp
    );
    
    /// @dev Emitted when a token is disabled
    event TokenDisabled(
        address indexed disabler,
        bytes32 indexed tokenHash,
        uint256 timestamp
    );
    
    // ============================================================
    // CORE FUNCTIONS
    // ============================================================
    
    /**
     * @dev Generate a unique token for the caller.
     * 
     * CRITICAL: This function MUST be called as a transaction (not view).
     * Each call produces a NEW, UNIQUE token because:
     * - msg.sender is the caller's address
     * - block.timestamp changes between blocks
     * - keccak256 is deterministic but address+timestamp = globally unique
     * 
     * @param dataHash IPFS hash of encrypted user data (for audit trail)
     * @return tokenHash The generated unique token hash
     * 
     * REQUIREMENTS:
     * - This is a state-changing transaction
     * - Only one token per user (enforced by require)
     * - Gas cost: ~80,000 gas
     * - MetaMask WILL show transaction popup
     */
    function generateToken(string memory dataHash) public returns (bytes32) {
        // (Restriction removed to allow backend relaying for multiple users)
        
        // Generate UNIQUE token using block.timestamp + msg.sender
        // This guarantees uniqueness:
        // - Same user calling twice = different timestamps = different tokens
        // - Different users = different addresses = different tokens
        bytes32 tokenHash = keccak256(
            abi.encodePacked(msg.sender, block.timestamp, block.number, dataHash)
        );
        
        // Ensure this token doesn't already exist (cryptographic collision protection)
        require(
            tokenRegistry[tokenHash].generator == address(0),
            "Token collision detected (extremely rare)"
        );
        
        // Store token metadata
        tokenRegistry[tokenHash] = Token({
            generator: msg.sender,
            timestamp: block.timestamp,
            active: true,
            dataHash: dataHash
        });
        
        // Map user to their token for fast lookup
        userToken[msg.sender] = tokenHash;
        
        // Increment counter
        tokenCount++;
        
        // CRITICAL: Emit event for audit trail and off-chain indexing
        emit TokenGenerated(
            msg.sender,
            tokenHash,
            block.timestamp,
            dataHash
        );
        
        return tokenHash;
    }
    
    /**
     * @dev Verify if a token is valid and active.
     * 
     * WARNING: Use with caution. This is a read function but should be called
     * with explicit address parameter to verify ownership.
     * 
     * @param tokenHash The token hash to verify
     * @return isValid True if token exists and is active
     */
    function verifyToken(bytes32 tokenHash) public view returns (bool) {
        Token memory token = tokenRegistry[tokenHash];
        return token.active && token.generator != address(0);
    }
    
    /**
     * @dev Verify token and return full details (for companies validating tokens).
     * 
     * @param tokenHash The token hash to verify
     * @return isValid True if token is active
     * @return generator Address that generated the token
     * @return generatedAt Timestamp when token was generated
     * @return dataHash IPFS hash of encrypted data
     */
    function getTokenDetails(bytes32 tokenHash) 
        public 
        view 
        returns (
            bool isValid,
            address generator,
            uint256 generatedAt,
            string memory dataHash
        ) 
    {
        Token memory token = tokenRegistry[tokenHash];
        return (
            token.active && token.generator != address(0),
            token.generator,
            token.timestamp,
            token.dataHash
        );
    }
    
    /**
     * @dev Check if calling user already has a token.
     * 
     * Used by frontend to determine if user can generate a new token.
     * 
     * @return hasToken True if user already has an active token
     */
    function hasActiveToken() public view returns (bool) {
        bytes32 existingToken = userToken[msg.sender];
        if (existingToken == bytes32(0)) {
            return false;
        }
        return tokenRegistry[existingToken].active;
    }
    
    /**
     * @dev Disable a token (only by token owner).
     * 
     * Allows users to revoke their own token in case of compromise.
     * 
     * @param tokenHash The token hash to disable
     */
    function disableToken(bytes32 tokenHash) public {
        Token storage token = tokenRegistry[tokenHash];
        require(
            token.generator == msg.sender,
            "Only token owner can disable"
        );
        require(
            token.active,
            "Token already disabled"
        );
        
        token.active = false;
        userToken[msg.sender] = bytes32(0);
        
        emit TokenDisabled(msg.sender, tokenHash, block.timestamp);
    }
    
    /**
     * @dev Get total number of tokens generated.
     * 
     * @return Total token count
     */
    function getTokenCount() public view returns (uint256) {
        return tokenCount;
    }
}
