import os, json, uuid, time
from py3xui import Api, Client, Inbound

host = os.getenv("XUI_HOST")
user = os.getenv("XUI_USERNAME")
password = os.getenv("XUI_PASSWORD")
iid = int(os.getenv("XUI_INBOUND_ID", "1"))

api = Api(host, user, password, use_tls_verify=False)
api.login()

print("=== Get inbound ===")
inbound = api.inbound.get_by_id(iid)
print(f"  id={inbound.id}, protocol={inbound.protocol}, port={inbound.port}")
print(f"  settings type={type(inbound.settings).__name__}")

# Show settings
if inbound.settings:
    try:
        s = json.loads(str(inbound.settings))
        print(f"  clients count={len(s.get('clients', []))}")
        print(f"  clients sample={[(c.get('email'), c.get('id','')[:8]) for c in s.get('clients',[])[:2]]}")
    except:
        print(f"  settings={str(inbound.settings)[:200]}")

# Add client via inbound.update
test_uuid = str(uuid.uuid4())
exp = int((time.time() + 30*86400)*1000)

new_client = {
    "id": test_uuid,
    "email": f"test_{int(time.time())}",
    "enable": True,
    "expiryTime": exp,
    "totalGB": 0,
    "flow": "xtls-rprx-vision",
    "limitIp": 0,
    "tgId": "",
    "subId": ""
}

print("\n=== Add client via inbound.update ===")
try:
    settings_str = str(inbound.settings) if inbound.settings else '{"clients": []}'
    settings = json.loads(settings_str)
    if "clients" not in settings:
        settings["clients"] = []
    settings["clients"].append(new_client)
    
    # py3xui uses pydantic models - need to set via setattr or use Inbound.update
    inbound.settings = json.dumps(settings)
    
    result = api.inbound.update(inbound)
    print(f"  result={result}")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Verify client added ===")
try:
    inbound2 = api.inbound.get_by_id(iid)
    settings2 = json.loads(str(inbound2.settings))
    for c in settings2.get("clients", []):
        if c.get("id") == test_uuid:
            print(f"  FOUND client: email={c.get('email')}, id={c.get('id')[:20]}...")
            break
    else:
        print("  Client NOT found after update")
except Exception as e:
    print(f"  verify FAIL: {e}")

# Delete client via inbound.update
print("\n=== Delete client via inbound.update ===")
try:
    inbound3 = api.inbound.get_by_id(iid)
    settings3 = json.loads(str(inbound3.settings))
    before = len(settings3.get("clients", []))
    settings3["clients"] = [c for c in settings3.get("clients", []) if c.get("id") != test_uuid]
    after = len(settings3["clients"])
    inbound3.settings = json.dumps(settings3)
    result = api.inbound.update(inbound3)
    print(f"  result={result}, clients before={before}, after={after}")
except Exception as e:
    print(f"  FAIL: {e}")
