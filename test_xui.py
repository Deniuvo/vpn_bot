import os, sys
sys.path.insert(0, '/root/vpn_bot')

host = os.getenv("XUI_HOST", "http://localhost:44875/3wBsYxDX2cUOynnPcl")
user = os.getenv("XUI_USERNAME", "admin")
pwd  = os.getenv("XUI_PASSWORD", "admin")
iid  = int(os.getenv("XUI_INBOUND_ID", "1"))

print(f"Host: {host}")
print(f"User: {user} / Pass: {pwd}")
print(f"Inbound ID: {iid}")

from py3xui import Api, Client
api = Api(host, user, pwd, use_tls_verify=False)

print("\n--- Login ---")
try:
    api.login()
    print("OK: logged in")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print("\n--- Get inbound ---")
try:
    inbound = api.inbound.get_by_id(iid)
    print(f"OK: inbound found - {inbound.remark}, protocol={inbound.protocol}")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- Create test client ---")
import uuid, time
try:
    c = Client(
        id=str(uuid.uuid4()),
        email="test_diag_delete_me",
        enable=True,
        expiry_time=int((time.time() + 30*86400)*1000),
        total_gb=0,
        flow="xtls-rprx-vision",
    )
    api.client.add(iid, [c])
    print(f"OK: client created")
    api.client.delete(iid, c.id)
    print("OK: client deleted")
except Exception as e:
    print(f"FAIL: {e}")
