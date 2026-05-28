import sys
sys.path.insert(0, '/root/vpn_bot')
from database import Database
import inspect

# Check the db instance
db_path = db.db_path if hasattr(db, 'db_path') else 'NO db_path'
print(f"DB PATH: {db_path}")

# Also check the class
print(f"DB class file: {inspect.getfile(Database)}")
