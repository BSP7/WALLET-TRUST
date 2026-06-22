# WALLET-TRUST - Secure Identity Authentication on Blockchain

This project provides a secure way to authenticate personal identification information using blockchain technology. The system allows users to generate secure tokens for their identity data, which can then be validated by companies through blockchain verification.

![WALLET-TRUST - Blockchain Identity Authentication](https://via.placeholder.com/800x400?text=WALLET-TRUST+Identity+Authentication)

## How It Works

### System Architecture

The WALLET-TRUST system consists of three main components:

1. **Frontend Web Application**: User and company interfaces for interacting with the system, built with modern web technologies.
2. **Backend API Server**: A Flask-based REST API that handles authentication, data processing, IPFS storage, and blockchain interactions.
3. **Blockchain Smart Contracts**: Solidity smart contracts deployed on the Ethereum network (e.g., Sepolia testnet) that provide immutable verification of token authenticity.

### Data Flow

1. **User Registration & Authentication**:
   - Users register with email and password
   - Authentication is handled via JWT tokens
   - Secure sessions are maintained

2. **Token Generation Process**:
   - User submits their personal identification information (PII)
   - Data is encrypted using AES-256 encryption
   - Encrypted data is stored on IPFS via Filebase
   - A unique token is generated and linked to the data
   - Token is registered on the Ethereum blockchain
   - User receives the token for future verification

3. **Token Validation Process**:
   - Companies request a token from users
   - Token is submitted to the validation endpoint
   - System verifies token authenticity on the blockchain
   - If valid, company receives confirmation of data authenticity
   - All validation attempts are logged for audit purposes

4. **Security Measures**:
   - All PII data is encrypted before storage
   - Only encrypted data is stored on IPFS
   - Blockchain provides tamper-proof verification
   - No PII is exposed during the validation process

## Features

- **Secure Token Generation**: Create cryptographically secure tokens for PII data
- **Blockchain Verification**: Validate tokens using Ethereum smart contracts
- **Decentralized Storage**: Store encrypted data on IPFS via Filebase
- **User Dashboard**: Manage personal tokens and account information
- **Company Portal**: Validate tokens and view validation history
- **Audit Logging**: Track all system activities for security purposes
- **Responsive Design**: User-friendly interface that works on all devices

## Project Structure

```
WALLET-TRUST/
├── backend/                 # Flask API server
│   ├── api/                 # API Routes and Middlewares
│   ├── auth/                # JWT and Auth Logic
│   ├── core/                # Core Blockchain, Crypto, and Storage Logic
│   ├── data/                # SQLite Database
│   ├── tests/               # Pytest Test Suite
│   ├── tools/               # Utility and Diagnostic Scripts
│   ├── app.py               # Main application entry point
│   ├── config.py            # Configuration logic
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # Web interface (React/Vite)
│   ├── src/                 # Source code
│   │   ├── components/      # UI Components
│   │   ├── pages/           # Application Pages
│   │   └── utils/           # Helper Utilities
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite Configuration
│
├── blockchain/              # Blockchain components
│   ├── contracts/           # Smart contract source code (Token_Auth.sol)
│   ├── scripts/             # Deployment scripts
│   ├── hardhat.config.js    # Hardhat configuration
│   └── package.json         # Blockchain dependencies
│
├── Docs/                    # Project documentation
├── .gitignore               # Git ignore file
└── README.md                # Project documentation
```

## Prerequisites

- **Python 3.11+**: For running the backend API server
- **Node.js 18+** and **npm**: For blockchain interactions and frontend development
- **Web Browser**: Chrome, Firefox, or Edge recommended
- **Ethereum Wallet**: For blockchain interactions (Metamask recommended)
- **Alchemy API Key**: For connecting to Ethereum networks
- **Filebase Account**: For IPFS storage access

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/BSP7/WALLET-TRUST.git
cd WALLET-TRUST
```

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory with the following variables:
   ```
   ALCHEMY_API_KEY=your_alchemy_api_key
   PRIVATE_KEY=your_ethereum_private_key
   CONTRACT_ADDRESS=your_deployed_contract_address
   FILEBASE_ACCESS_KEY=your_filebase_access_key
   FILEBASE_SECRET_KEY=your_filebase_secret_key
   BUCKET_NAME=your_filebase_bucket_name
   ENCRYPTION_KEY=your_base64_encoded_aes_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

### 3. Blockchain Setup

1. Navigate to the blockchain directory:
   ```bash
   cd ../blockchain
   ```

2. Install the required Node.js packages:
   ```bash
   npm install
   ```

3. Create a `.env` file in the blockchain directory with:
   ```
   ALCHEMY_API_KEY=your_alchemy_api_key
   PRIVATE_KEY=your_ethereum_private_key
   ```

4. Deploy the smart contract (optional - only if deploying a new contract):
   ```bash
   npx hardhat run scripts/deploy.js --network sepolia
   ```

### 4. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend server:
   ```bash
   npm run dev
   ```

## API Endpoints

The backend provides RESTful API endpoints securely hosted over HTTP. Ensure that the required JWT `Authorization` header is passed for protected endpoints.

- **Authentication**: `/api/auth/register`, `/api/auth/login`, `/api/auth/profile`
- **Documents**: `/api/documents/upload`, `/api/documents/<id>`, `/api/documents/<id>/download`
- **Blockchain Tokens**: `/api/blockchain/generate_token`, `/api/blockchain/verify_token`
- **Company Validation**: `/api/company/verify`, `/api/company/validations`

## Testing

### Running Backend Tests

The project includes comprehensive unit and integration tests under `backend/tests/`:

```bash
cd backend
python -m pytest tests/ -v
```

To run coverage tests:
```bash
python -m pytest --cov=. tests/
```

## Troubleshooting

- **CORS Issues**: Make sure the backend server and frontend server are properly communicating over their respective ports.
- **Blockchain Connection Errors**: Verify your Alchemy API key and network settings.
- **Token Validation Failures**: Ensure the contract address is correctly set in your `.env` file and the blockchain has finished confirming your block.
- **File Storage Issues**: Check your Filebase credentials and bucket configuration.
- **JWT Authentication Errors**: Verify that your `JWT_SECRET_KEY` is properly set.

## Security Considerations

- **Data Encryption**: All PII data is encrypted using AES-256-GCM before storage.
- **Blockchain Verification**: Tokens are verified on the blockchain for authenticity, matching hashes securely.
- **Password Security**: User passwords are securely hashed.
- **Environment Variables**: All sensitive configuration is stored in `.env` variables and excluded from version control.
- **Access Control**: Role-based JWT authentication restricts users vs. companies from accessing unpermitted endpoints.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.