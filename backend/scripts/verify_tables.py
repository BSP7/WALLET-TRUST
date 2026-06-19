"""Verify and display database tables structure."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

db_name = None
try:
    db_name = make_url(db_url).database
except Exception:
    db_name = None

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"[INFO] Tables in {db_name or 'database'}:")
for table in tables:
    print(f'  ✓ {table}')

print('\n[INFO] Users table structure:')
print('  Column Name              Type                 Nullable')
print('  ' + '-' * 60)
columns = inspector.get_columns('users')
for col in columns:
    col_type = str(col['type'])
    nullable = 'YES' if col['nullable'] else 'NO'
    print(f"  {col['name']:<24} {col_type:<20} {nullable}")

print('\n[INFO] Documents table structure:')
print('  Column Name              Type                 Nullable')
print('  ' + '-' * 60)
columns = inspector.get_columns('documents')
for col in columns:
    col_type = str(col['type'])
    nullable = 'YES' if col['nullable'] else 'NO'
    print(f"  {col['name']:<24} {col_type:<20} {nullable}")

print('\n[INFO] ValidationHistory table structure:')
print('  Column Name              Type                 Nullable')
print('  ' + '-' * 60)
columns = inspector.get_columns('validation_history')
for col in columns:
    col_type = str(col['type'])
    nullable = 'YES' if col['nullable'] else 'NO'
    print(f"  {col['name']:<24} {col_type:<20} {nullable}")

print('\n[DONE] ✅ All tables verified successfully!')
