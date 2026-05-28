import sys, os
sys.path.insert(0, '/root/vpn_bot')
from xui_api import XUIManager
m = XUIManager()
m._ensure_login()
link = m.get_vless_link('test-uuid')
print(f"LINK: {link}")
print(f"REMARK from env: {os.getenv('XUI_REMARK', 'NOT SET')}")
