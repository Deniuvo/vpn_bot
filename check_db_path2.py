import sys
sys.path.insert(0, '/root/vpn_bot')
import database
print("MODULE ATTRS:", [a for a in dir(database) if not a.startswith('_')])
if hasattr(database, 'db'):
    db = database.db
    print(f"DB PATH: {db.db_path if hasattr(db, 'db_path') else 'NO path'}")
else:
    print("NO db instance")

# Check the Database class
from database import Database
print(f"Default DB path in class: {Database.DEFAULT_DB_PATH if hasattr(Database, 'DEFAULT_DB_PATH') else 'NO DEFAULT_DB_PATH'}")
