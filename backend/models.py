"""
Database models for WALLET-TRUST application.

This module defines SQLAlchemy models for:
- User: Individual users with authentication
- Company: Organizations that validate tokens
- Validation: Token validation records
- Document: User documents stored on blockchain
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class User(db.Model):
    """
    User account model.
    
    Stores user authentication data and profile information.
    """
    __tablename__ = 'users'
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    dob = Column(String(50))
    password_hash = Column(String(128), nullable=False)
    password_salt = Column(String(64), nullable=False)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    
    # Relationships
    tokens = relationship('Token', back_populates='user', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')
    validation_history = relationship('ValidationHistory', back_populates='user', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert user to dictionary (excludes password)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'dob': self.dob,
            'created_at': self.created_at,
            'tokens': [token.id for token in self.tokens],
            'documents': [doc.id for doc in self.documents]
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


class Company(db.Model):
    """
    Company/Organization model.
    
    Represents organizations that validate user tokens.
    """
    __tablename__ = 'companies'
    
    id = Column(String(100), primary_key=True)
    company_name = Column(String(200), nullable=False)
    business_type = Column(String(100))
    registration_number = Column(String(100), unique=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    address = Column(Text)
    password_hash = Column(String(128), nullable=False)
    password_salt = Column(String(64), nullable=False)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    
    # Relationships
    validations = relationship('Validation', back_populates='company', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert company to dictionary (excludes password)."""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'business_type': self.business_type,
            'registration_number': self.registration_number,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at,
            'validations': [val.id for val in self.validations]
        }
    
    def __repr__(self):
        return f'<Company {self.company_name}>'


class Validation(db.Model):
    """
    Token validation record.
    
    Stores validation requests and results from companies.
    """
    __tablename__ = 'validations'
    
    id = Column(String(100), primary_key=True)
    company_id = Column(String(100), ForeignKey('companies.id'), nullable=False, index=True)
    token = Column(String(200), nullable=False, index=True)
    purpose = Column(String(100))
    is_valid = Column(Boolean, default=False)
    tx_hash = Column(String(200), index=True)
    validation_tx_hash = Column(String(200), index=True)
    timestamp = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    
    # Relationships
    company = relationship('Company', back_populates='validations')
    
    def to_dict(self):
        """Convert validation to dictionary."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'token': self.token,
            'purpose': self.purpose,
            'is_valid': self.is_valid,
            'tx_hash': self.tx_hash,
            'validation_tx_hash': self.validation_tx_hash,
            'timestamp': self.timestamp
        }
    
    def __repr__(self):
        return f'<Validation {self.id}>'


class Token(db.Model):
    """
    User token model.
    
    Stores tokens generated for users on the blockchain.
    """
    __tablename__ = 'tokens'
    
    id = Column(String(100), primary_key=True)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False, index=True)
    token_id = Column(Integer, unique=True, index=True)
    document_hash = Column(String(200))
    tx_hash = Column(String(200), index=True)
    block_number = Column(Integer)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    
    # Relationships
    user = relationship('User', back_populates='tokens')
    
    def to_dict(self):
        """Convert token to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token_id': self.token_id,
            'document_hash': self.document_hash,
            'tx_hash': self.tx_hash,
            'block_number': self.block_number,
            'created_at': self.created_at
        }
    
    def __repr__(self):
        return f'<Token {self.token_id}>'


class Document(db.Model):
    """
    User document model.
    
    Stores encrypted documents associated with users.
    """
    __tablename__ = 'documents'
    
    id = Column(String(100), primary_key=True)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_hash = Column(String(200))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    encrypted = Column(Boolean, default=True)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    meta_data = Column('metadata', JSON)
    
    # Relationships
    user = relationship('User', back_populates='documents')
    validation_history = relationship('ValidationHistory', back_populates='document', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'encrypted': self.encrypted,
            'created_at': self.created_at,
            'metadata': self.meta_data
        }
    
    def __repr__(self):
        return f'<Document {self.filename}>'

class ValidationHistory(db.Model):
    """
    Validation history model.
    
    Stores validation records for documents and users.
    """
    __tablename__ = 'validation_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False, index=True)
    document_id = Column(String(100), ForeignKey('documents.id'), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False, default=False)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())
    
    # Relationships
    user = relationship('User', back_populates='validation_history')
    document = relationship('Document', back_populates='validation_history')
    
    def to_dict(self):
        """Convert validation history to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_id': self.document_id,
            'is_valid': self.is_valid,
            'created_at': self.created_at
        }
    
    def __repr__(self):
        return f'<ValidationHistory {self.id}>'


class BlockchainKV(db.Model):
    """Generic key/value storage for blockchain-related data.

    Useful for persisting lightweight blockchain events, tx hashes, sync cursors,
    or other structured payloads without changing schema frequently.
    """

    __tablename__ = 'blockchain_kv'

    __table_args__ = (
        Index('idx_blockchain_kv_user_data_key', 'user_id', 'data_key'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False, index=True)
    key = Column('data_key', String(255), nullable=False, index=True)
    value = Column(JSON)
    created_at = Column(Float, nullable=False, default=lambda: datetime.utcnow().timestamp())

    user = relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at,
        }

    def __repr__(self):
        return f'<BlockchainKV {self.key}>'