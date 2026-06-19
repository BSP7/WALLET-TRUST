"""Migration script to populate the application database from existing JSON files.

This script:
1. Reads data from users.json, companies.json, validations.json
2. Migrates them into the configured SQLAlchemy database (MySQL by default)
3. Preserves existing data and relationships

Run this ONCE after setting up your database connection and before deleting JSON files.
"""

import json
import os
import sys
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from app_factory import create_app
from models import db, User, Company, Validation
from db_service import UserService, CompanyService, ValidationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json_file(filepath):
    """Load JSON file if it exists."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return {}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return {}


def migrate_users(users_data):
    """Migrate users from JSON to database."""
    logger.info(f"Migrating {len(users_data)} users...")
    
    migrated = 0
    errors = 0
    
    for user_id, user_info in users_data.items():
        try:
            # Check if user already exists
            existing = UserService.get_user_by_email(user_info['email'])
            if existing:
                logger.info(f"User already exists: {user_info['email']}")
                continue
            
            # Create user
            UserService.create_user(
                user_id=user_info['id'],
                name=user_info['name'],
                email=user_info['email'],
                password_hash=user_info['password_hash'],
                password_salt=user_info['password_salt'],
                phone=user_info.get('phone'),
                dob=user_info.get('dob')
            )
            migrated += 1
            logger.info(f"Migrated user: {user_info['email']}")
            
        except Exception as e:
            errors += 1
            logger.error(f"Error migrating user {user_id}: {e}")
    
    logger.info(f"Users migration complete: {migrated} migrated, {errors} errors")
    return migrated, errors


def migrate_companies(companies_data):
    """Migrate companies from JSON to database."""
    logger.info(f"Migrating {len(companies_data)} companies...")
    
    migrated = 0
    errors = 0
    
    for company_id, company_info in companies_data.items():
        try:
            # Check if company already exists
            existing = CompanyService.get_company_by_email(company_info['email'])
            if existing:
                logger.info(f"Company already exists: {company_info['email']}")
                continue
            
            # Create company
            CompanyService.create_company(
                company_id=company_info['id'],
                company_name=company_info['company_name'],
                email=company_info['email'],
                password_hash=company_info['password_hash'],
                password_salt=company_info['password_salt'],
                business_type=company_info.get('business_type'),
                registration_number=company_info.get('registration_number'),
                phone=company_info.get('phone'),
                address=company_info.get('address')
            )
            migrated += 1
            logger.info(f"Migrated company: {company_info['company_name']}")
            
        except Exception as e:
            errors += 1
            logger.error(f"Error migrating company {company_id}: {e}")
    
    logger.info(f"Companies migration complete: {migrated} migrated, {errors} errors")
    return migrated, errors


def migrate_validations(validations_data):
    """Migrate validations from JSON to database."""
    logger.info(f"Migrating {len(validations_data)} validations...")
    
    migrated = 0
    errors = 0
    
    for validation_id, validation_info in validations_data.items():
        try:
            # Check if validation already exists
            existing = ValidationService.get_validation_by_id(validation_info['id'])
            if existing:
                logger.info(f"Validation already exists: {validation_info['id']}")
                continue
            
            # Create validation
            ValidationService.create_validation(
                validation_id=validation_info['id'],
                company_id=validation_info['company_id'],
                token=validation_info['token'],
                purpose=validation_info.get('purpose'),
                is_valid=validation_info.get('is_valid', False),
                tx_hash=validation_info.get('tx_hash'),
                validation_tx_hash=validation_info.get('validation_tx_hash')
            )
            migrated += 1
            logger.info(f"Migrated validation: {validation_info['id']}")
            
        except Exception as e:
            errors += 1
            logger.error(f"Error migrating validation {validation_id}: {e}")
    
    logger.info(f"Validations migration complete: {migrated} migrated, {errors} errors")
    return migrated, errors


def main():
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("Starting JSON to Database Migration")
    logger.info("=" * 60)
    
    # Create Flask app to initialize database
    app = create_app()
    
    with app.app_context():
        # Load JSON files
        backend_dir = Path(__file__).parent
        users_data = load_json_file(backend_dir / 'users.json')
        companies_data = load_json_file(backend_dir / 'companies.json')
        validations_data = load_json_file(backend_dir / 'validations.json')
        
        # Migrate data
        logger.info("Starting migration process...")
        
        users_migrated, users_errors = migrate_users(users_data)
        companies_migrated, companies_errors = migrate_companies(companies_data)
        validations_migrated, validations_errors = migrate_validations(validations_data)
        
        # Summary
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Users:       {users_migrated} migrated, {users_errors} errors")
        logger.info(f"Companies:   {companies_migrated} migrated, {companies_errors} errors")
        logger.info(f"Validations: {validations_migrated} migrated, {validations_errors} errors")
        logger.info("=" * 60)
        
        total_migrated = users_migrated + companies_migrated + validations_migrated
        total_errors = users_errors + companies_errors + validations_errors
        
        if total_errors > 0:
            logger.warning(f"⚠️  Migration completed with {total_errors} errors")
        else:
            logger.info(f"✅ Migration completed successfully! {total_migrated} records migrated")


if __name__ == '__main__':
    main()
