import sys
import os
os.chdir('/root/vpn_bot')
sys.path.insert(0, '/root/vpn_bot')
from database import db
db.init_db()
print("init_db OK from /root/vpn_bot")
