import os
import sys
sys.path.insert(0, '/root/vpn_bot')

from xui_api import XUIManager

os.environ.setdefault('XUI_INBOUND_ID', '2')

mgr = XUIManager()
mgr._ensure_login()

cfg = mgr._load_inbound_config()
print(f"port={cfg['port']}, sni={cfg['sni']}, pbk={cfg['pbk'][:20] if cfg['pbk'] else 'EMPTY'}..., sid={cfg['sid'][:16] if cfg['sid'] else 'EMPTY'}")

link = mgr.get_vless_link("test-uuid-1234", remark=f"CloudHapp-Test")
print(f"\nvless link:\n{link}")
