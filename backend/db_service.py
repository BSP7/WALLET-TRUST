"""
Database service layer for WALLET-TRUST application.

Provides high-level database operations for:
- User management
- Company management
- Token validation
- Document storage
"""

import logging
import time
from typing import Optional, List, Dict, Any
from models import db, User, Company, Validation, Token, Document

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related database operations."""
    
    @staticmethod
    def create_user(user_id: str, name: str, email: str, password_hash: str, 
                    password_salt: str, phone: Optional[str] = None, dob: Optional[str] = None) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_id: Unique user identifier
            name: User's full name
            email: User's email address
            password_hash: Hashed password
            password_salt: Password salt
            phone: Phone number (optional)
            dob: Date of birth (optional)
        
        Returns:
            Created User object
        
        Raises:
            Exception: If user already exists or database error
        """
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            user = User(
                id=user_id,
                name=name,
                email=email,
                password_hash=password_hash,
                password_salt=password_salt,
                phone=phone,
                dob=dob,
                created_at=time.time()
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"Created user: {user_id} ({email})")
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def update_user(user_id: str, **kwargs) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID to update
            **kwargs: Fields to update (name, email, phone, dob, etc.)
        
        Returns:
            Updated User object or None if not found
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            for key, value in kwargs.items():
                if hasattr(user, key) and key not in ['id', 'created_at']:
                    setattr(user, key, value)
            
            db.session.commit()
            logger.info(f"Updated user: {user_id}")
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete a user."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            db.session.delete(user)
            db.session.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise


class CompanyService:
    """Service for company-related database operations."""
    
    @staticmethod
    def create_company(company_id: str, company_name: str, email: str, 
                      password_hash: str, password_salt: str, 
                      business_type: Optional[str] = None, registration_number: Optional[str] = None,
                      phone: Optional[str] = None, address: Optional[str] = None) -> Company:
        """
        Create a new company in the database.
        
        Args:
            company_id: Unique company identifier
            company_name: Company name
            email: Company email address
            password_hash: Hashed password
            password_salt: Password salt
            business_type: Type of business (optional)
            registration_number: Registration number (optional)
            phone: Phone number (optional)
            address: Company address (optional)
        
        Returns:
            Created Company object
        """
        try:
            # Check if company already exists
            existing_company = Company.query.filter_by(email=email).first()
            if existing_company:
                raise ValueError(f"Company with email {email} already exists")
            
            company = Company(
                id=company_id,
                company_name=company_name,
                email=email,
                password_hash=password_hash,
                password_salt=password_salt,
                business_type=business_type,
                registration_number=registration_number,
                phone=phone,
                address=address,
                created_at=time.time()
            )
            
            db.session.add(company)
            db.session.commit()
            
            logger.info(f"Created company: {company_id} ({company_name})")
            return company
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create company: {e}")
            raise
    
    @staticmethod
    def get_company_by_id(company_id: str) -> Optional[Company]:
        """Get company by ID."""
        return Company.query.get(company_id)
    
    @staticmethod
    def get_company_by_email(email: str) -> Optional[Company]:
        """Get company by email."""
        return Company.query.filter_by(email=email).first()
    
    @staticmethod
    def update_company(company_id: str, **kwargs) -> Optional[Company]:
        """Update company information."""
        try:
            company = Company.query.get(company_id)
            if not company:
                return None
            
            for key, value in kwargs.items():
                if hasattr(company, key) and key not in ['id', 'created_at']:
                    setattr(company, key, value)
            
            db.session.commit()
            logger.info(f"Updated company: {company_id}")
            return company
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update company {company_id}: {e}")
            raise


class ValidationService:
    """Service for validation-related database operations."""
    
    @staticmethod
    def create_validation(validation_id: str, company_id: str, token: str,
                         purpose: Optional[str] = None, is_valid: bool = False,
                         tx_hash: Optional[str] = None, validation_tx_hash: Optional[str] = None) -> Validation:
        """Create a new validation record."""
        try:
            validation = Validation(
                id=validation_id,
                company_id=company_id,
                token=token,
                purpose=purpose,
                is_valid=is_valid,
                tx_hash=tx_hash,
                validation_tx_hash=validation_tx_hash,
                timestamp=time.time()
            )
            
            db.session.add(validation)
            db.session.commit()
            
            logger.info(f"Created validation: {validation_id} for company {company_id}")
            return validation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create validation: {e}")
            raise
    
    @staticmethod
    def get_validation_by_id(validation_id: str) -> Optional[Validation]:
        """Get validation by ID."""
        return Validation.query.get(validation_id)
    
    @staticmethod
    def get_validations_by_company(company_id: str) -> List[Validation]:
        """Get all validations for a company."""
        return Validation.query.filter_by(company_id=company_id).all()
    
    @staticmethod
    def get_validations_by_token(token: str) -> List[Validation]:
        """Get all validations for a specific token."""
        return Validation.query.filter_by(token=token).all()
    
    @staticmethod
    def update_validation(validation_id: str, **kwargs) -> Optional[Validation]:
        """Update validation status."""
        try:
            validation = Validation.query.get(validation_id)
            if not validation:
                return None
            
            for key, value in kwargs.items():
                if hasattr(validation, key) and key not in ['id', 'timestamp']:
                    setattr(validation, key, value)
            
            db.session.commit()
            logger.info(f"Updated validation: {validation_id}")
            return validation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update validation {validation_id}: {e}")
            raise


class TokenService:
    """Service for token-related database operations."""
    
    @staticmethod
    def create_token(token_id_str: str, user_id: str, token_id: Optional[int],
                    document_hash: Optional[str] = None, tx_hash: Optional[str] = None,
                    block_number: Optional[int] = None) -> Token:
        """Create a new token record."""
        try:
            token = Token(
                id=token_id_str,
                user_id=user_id,
                token_id=token_id,
                document_hash=document_hash,
                tx_hash=tx_hash,
                block_number=block_number,
                created_at=time.time()
            )
            
            db.session.add(token)
            db.session.commit()
            
            logger.info(f"Created token: {token_id_str} for user {user_id}")
            return token
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create token: {e}")
            raise
    
    @staticmethod
    def get_token_by_id(token_id: str) -> Optional[Token]:
        """Get token by ID."""
        return Token.query.get(token_id)
    
    @staticmethod
    def get_token_by_token_id(token_id: int) -> Optional[Token]:
        """Get token by blockchain token ID."""
        return Token.query.filter_by(token_id=token_id).first()
    
    @staticmethod
    def get_tokens_by_user(user_id: str) -> List[Token]:
        """Get all tokens for a user."""
        return Token.query.filter_by(user_id=user_id).all()


class DocumentService:
    """Service for document-related database operations."""
    
    @staticmethod
    def create_document(doc_id: str, user_id: str, filename: str,
                       file_path: Optional[str] = None, file_hash: Optional[str] = None,
                       file_size: Optional[int] = None, mime_type: Optional[str] = None,
                       encrypted: bool = True, metadata: Optional[dict] = None) -> Document:
        """Create a new document record."""
        try:
            document = Document(
                id=doc_id,
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                encrypted=encrypted,
                created_at=time.time(),
                meta_data=metadata
            )
            
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"Created document: {doc_id} for user {user_id}")
            return document
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create document: {e}")
            raise
    
    @staticmethod
    def get_document_by_id(doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return Document.query.get(doc_id)
    
    @staticmethod
    def get_documents_by_user(user_id: str) -> List[Document]:
        """Get all documents for a user."""
        return Document.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def delete_document(doc_id: str) -> bool:
        """Delete a document."""
        try:
            document = Document.query.get(doc_id)
            if not document:
                return False
            
            db.session.delete(document)
            db.session.commit()
            logger.info(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
