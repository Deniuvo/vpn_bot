import os, json, uuid, time, requests
from py3xui import Api, Inbound

host = os.getenv("XUI_HOST")
user = os.getenv("XUI_USERNAME")
password = os.getenv("XUI_PASSWORD")
iid = int(os.getenv("XUI_INBOUND_ID", "1"))

api = Api(host, user, password, use_tls_verify=False)
api.login()

# Get cookies
session_cookie = getattr(api, '_session', '')
csrf_token = getattr(api, '_csrf_token', '')
cookies_dict = {'3x-ui': session_cookie}

print(f"session_cookie type={type(session_cookie).__name__}, len={len(session_cookie) if isinstance(session_cookie, str) else 'N/A'}")
print(f"csrf_token type={type(csrf_token).__name__}")

print("\n=== Test manual update with py3xui cookies ===")

# Get current inbound
inbound = api.inbound.get_by_id(iid)
settings = json.loads(str(inbound.settings))
if "clients" not in settings:
    settings["clients"] = []

test_uuid = str(uuid.uuid4())
exp = int((time.time() + 30*86400)*1000)
new_client = {
    "id": test_uuid,
    "email": f"test2_{int(time.time())}",
    "enable": True,
    "expiryTime": exp,
    "totalGB": 0,
    "flow": "xtls-rprx-vision",
    "limitIp": 0,
    "tgId": "",
    "subId": ""
}
settings["clients"].append(new_client)

# Build payload matching 3X-UI update API
inbound.settings = json.dumps(settings)

# Try with requests directly
headers = {
    "Accept": "application/json",
    "X-CSRF-Token": csrf_token if isinstance(csrf_token, str) else "",
}

s = requests.Session()
s.verify = False
s.cookies.update(cookies_dict)

# Option 1: POST /panel/api/inbounds/update
update_data = inbound.model_dump() if hasattr(inbound, 'model_dump') else inbound.__dict__
print(f"  update_data type={type(update_data).__name__}")
print(f"  update_data keys={list(update_data.keys()) if isinstance(update_data, dict) else 'N/A'}")

r1 = s.post(f"{host}/panel/api/inbounds/update", json=update_data, headers=headers)
print(f"  POST /update: status={r1.status_code}, body={r1.text[:200]!r}")

# Option 2: POST /panel/api/inbounds/update with form data
r2 = s.post(f"{host}/panel/api/inbounds/update", data=update_data, headers=headers)
print(f"  POST /update (form): status={r2.status_code}, body={r2.text[:200]!r}")

# Option 3: POST /panel/api/inbounds with PUT semantics
r3 = s.post(f"{host}/panel/api/inbounds", json=update_data, headers=headers)
print(f"  POST /inbounds: status={r3.status_code}, body={r3.text[:200]!r}")

# Option 4: GET to check if panel is responsive at all
r4 = s.get(f"{host}/panel/api/inbounds/get/{iid}", headers=headers)
print(f"  GET /get/{iid}: status={r4.status_code}, body={r4.text[:200]!r}")

# Clean up - remove test client
print("\n=== Clean up ===")
inbound2 = api.inbound.get_by_id(iid)
settings2 = json.loads(str(inbound2.settings))
before = len(settings2.get("clients", []))
settings2["clients"] = [c for c in settings2.get("clients", []) if not c.get("email", "").startswith("test2_")]
after = len(settings2["clients"])
inbound2.settings = json.dumps(settings2)
api.inbound.update(inbound2)
print(f"  removed test clients, before={before}, after={after}")
