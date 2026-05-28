import sys
sys.path.insert(0, "/root/vpn_bot")
from database import db
db.init_db()
print("init_db OK")
