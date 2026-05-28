import os, json, requests
from py3xui import Api

host = os.getenv("XUI_HOST")
user = os.getenv("XUI_USERNAME")
password = os.getenv("XUI_PASSWORD")
iid = int(os.getenv("XUI_INBOUND_ID", "1"))

api = Api(host, user, password, use_tls_verify=False)
api.login()

session_cookie = api._session
csrf_token = api._csrf_token

headers = {
    "Accept": "application/json",
    "X-CSRF-Token": csrf_token,
}

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': session_cookie})

# Get raw inbound data
r = s.get(f"{host}/panel/api/inbounds/get/{iid}", headers=headers)
print(f"GET /get/{iid}: status={r.status_code}")
try:
    data = r.json()
    print(f"success={data.get('success')}")
    obj = data.get('obj', {})
    print(f"inbound keys={list(obj.keys())}")
    settings_raw = obj.get('settings', '')
    print(f"settings type={type(settings_raw).__name__}, len={len(settings_raw) if isinstance(settings_raw, str) else 'N/A'}")
    print(f"settings preview={settings_raw[:300]!r}")
    
    settings = json.loads(settings_raw)
    print(f"clients count={len(settings.get('clients', []))}")
    print(f"clients={[(c.get('email'), c.get('id','')[:8]) for c in settings.get('clients', [])[:3]]}")
except Exception as e:
    print(f"ERROR: {e}")
    print(f"raw response={r.text[:500]!r}")

# Try raw update
print("\n=== Try raw update ===")
test_uuid = __import__('uuid').uuid4().hex
new_client = {
    "id": test_uuid,
    "email": f"rawtest_{int(__import__('time').time())}",
    "enable": True,
    "expiryTime": int((__import__('time').time() + 30*86400)*1000),
    "totalGB": 0,
    "flow": "xtls-rprx-vision",
    "limitIp": 0,
    "tgId": "",
    "subId": ""
}

settings['clients'].append(new_client)

# Build update payload exactly as 3X-UI expects
payload = {
    "id": iid,
    "settings": json.dumps(settings),
    "remark": obj.get('remark', ''),
    "enable": obj.get('enable', True),
    "listen": obj.get('listen', ''),
    "port": obj.get('port', 443),
    "protocol": obj.get('protocol', 'vless'),
    "tag": obj.get('tag', ''),
    "sniffing": json.dumps(obj.get('sniffing', {})) if isinstance(obj.get('sniffing'), dict) else obj.get('sniffing', ''),
    "streamSettings": json.dumps(obj.get('streamSettings', {})) if isinstance(obj.get('streamSettings'), dict) else obj.get('streamSettings', ''),
    "allocate": json.dumps(obj.get('allocate', {})) if isinstance(obj.get('allocate'), dict) else obj.get('allocate', ''),
}

r2 = s.post(f"{host}/panel/api/inbounds/update", json=payload, headers=headers)
print(f"POST /update (json): status={r2.status_code}, body={r2.text[:300]!r}")

# Also try with inbound dict
payload2 = dict(obj)
payload2['settings'] = json.dumps(settings)
for k in ['sniffing', 'streamSettings', 'allocate']:
    if k in payload2 and isinstance(payload2[k], dict):
        payload2[k] = json.dumps(payload2[k])

r3 = s.post(f"{host}/panel/api/inbounds/update", json=payload2, headers=headers)
print(f"POST /update (full obj): status={r3.status_code}, body={r3.text[:300]!r}")
