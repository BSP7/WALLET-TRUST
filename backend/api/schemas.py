# backend/api/schemas.py
"""
Request and response validation schemas for WALLET-TRUST API.

Uses Pydantic for runtime type checking and data validation.
"""

from pydantic import BaseModel, Field, EmailStr, validator, constr
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class UserRegistrationRequest(BaseModel):
    """User registration request validation."""
    name: constr(min_length=2, max_length=100)
    email: EmailStr
    password: constr(min_length=12, max_length=128)
    phone: Optional[constr(max_length=20)] = None
    dob: Optional[str] = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in '!@#$%^&*' for c in v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('dob')
    def validate_dob_format(cls, v):
        """Validate date of birth format (YYYY-MM-DD)."""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class UserLoginRequest(BaseModel):
    """User login request validation."""
    email: EmailStr
    password: constr(min_length=1, max_length=128)


class UserProfileUpdateRequest(BaseModel):
    """User profile update request validation (partial updates)."""

    name: Optional[constr(min_length=2, max_length=100)] = None
    email: Optional[EmailStr] = None
    phone: Optional[constr(max_length=20)] = None
    dob: Optional[str] = None

    @validator('dob')
    def validate_dob_format(cls, v):
        """Validate date of birth format (YYYY-MM-DD)."""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v

    class Config:
        extra = 'forbid'


class TokenRefreshRequest(BaseModel):
    """Token refresh request validation."""
    refresh_token: constr(min_length=10)


class DocumentUploadRequest(BaseModel):
    """Document upload metadata validation."""
    title: constr(min_length=1, max_length=255)
    doc_type: str = Field(..., description="Document type (passport, driver_license, national_id)")
    
    @validator('doc_type')
    def validate_doc_type(cls, v):
        """Validate document type is supported."""
        valid_types = {'passport', 'driver_license', 'national_id', 'id'}
        if v not in valid_types:
            raise ValueError(f'Document type must be one of: {valid_types}')
        return v


class TokenGenerationRequest(BaseModel):
    """Token generation request validation."""
    user_id: constr(min_length=1, max_length=255)
    government_id_number: Optional[constr(max_length=50)] = None


class TokenValidationRequest(BaseModel):
    """Token validation request validation."""
    token: constr(min_length=4)
    purpose: Optional[str] = None


class EncryptionPayloadRequest(BaseModel):
    """PII encryption request validation."""
    name: constr(min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    dob: Optional[str] = None
    phone: Optional[constr(max_length=20)] = None
    id_type: str
    id_number: constr(min_length=1, max_length=50)
    user_id: Optional[str] = None
    
    @validator('id_type')
    def validate_id_type(cls, v):
        """Validate ID type."""
        valid_types = {'passport', 'national_id', 'driver_license', 'ssn', 'tax_id'}
        if v not in valid_types:
            raise ValueError(f'ID type must be one of: {valid_types}')
        return v


class CompanyRegistrationRequest(BaseModel):
    """Company registration request validation."""
    company_name: constr(min_length=2, max_length=255)
    business_type: str
    registration_number: constr(min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[constr(max_length=20)] = None
    address: Optional[constr(max_length=500)] = None
    password: constr(min_length=12, max_length=128)


class UserResponse(BaseModel):
    """User response schema."""
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    created_at: float
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(default=86400, description="Expiration in seconds")


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    title: str
    type: str
    file_url: str
    uploaded_at: str
    tx_hash: Optional[str] = None


class BlockchainTransactionResponse(BaseModel):
    """Blockchain transaction response schema."""
    success: bool
    tx_hash: Optional[str] = None
    ipfs_hash: Optional[str] = None
    etherscan_url: Optional[str] = None
    status: str = "pending"
    message: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = "healthy"
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    version: str = "1.0.0"
    blockchain_connected: Optional[bool] = None
    storage_connected: Optional[bool] = None
