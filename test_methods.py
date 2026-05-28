import os, json, uuid, time
from py3xui import Api, Client

host = os.getenv("XUI_HOST", "http://localhost:44875/3wBsYxDX2cUOynnPcl")
user = os.getenv("XUI_USERNAME", "root")
password = os.getenv("XUI_PASSWORD", "")
iid = int(os.getenv("XUI_INBOUND_ID", "1"))

api = Api(host, user, password, use_tls_verify=False)
api.login()

print("=== api.client methods ===")
for name in sorted(dir(api.client)):
    if not name.startswith('_'):
        print(f"  {name}")

print("\n=== api.inbound methods ===")
for name in sorted(dir(api.inbound)):
    if not name.startswith('_'):
        print(f"  {name}")

print("\n=== Test get inbounds ===")
try:
    inbounds = api.inbound.get_list()
    print(f"  inbounds type={type(inbounds).__name__}")
    if isinstance(inbounds, list):
        for ib in inbounds:
            print(f"  id={ib.id}, protocol={ib.protocol}, port={ib.port}")
    else:
        print(f"  value={inbounds}")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Test get single inbound ===")
try:
    inbound = api.inbound.get_by_id(iid)
    print(f"  inbound type={type(inbound).__name__}")
    print(f"  id={inbound.id}, protocol={inbound.protocol}")
    print(f"  settings len={len(inbound.settings or '')}")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Test add client ===")
try:
    test_uuid = str(uuid.uuid4())
    exp = int((time.time() + 30*86400)*1000)
    client = Client(
        id=test_uuid,
        email="test_py3xui_del",
        enable=True,
        expiry_time=exp,
        total_gb=0,
        flow="xtls-rprx-vision",
        limit_ip=0,
        sub_id="",
    )
    result = api.client.add(iid, [client])
    print(f"  result type={type(result).__name__}")
    print(f"  result={result}")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Test delete client ===")
try:
    result = api.client.delete(iid, test_uuid)
    print(f"  delete result={result}")
except Exception as e:
    print(f"  delete FAIL: {e}")
