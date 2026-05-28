import os, json, uuid, time, requests
from py3xui import Api

host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

# 1. Get inbound
r = s.get(f'{host}/panel/api/inbounds/get/1', headers=h)
print(f"raw obj keys={list(r.json()['obj'].keys())}")
print(f"settings value={r.json()['obj'].get('settings')!r}")
obj = r.json()['obj']
raw_settings = obj.get('settings')
if raw_settings is None:
    settings = {"clients": [], "decryption": "none", "fallbacks": []}
elif isinstance(raw_settings, dict):
    settings = raw_settings
else:
    settings = json.loads(raw_settings)
if 'clients' not in settings:
    settings['clients'] = []
print(f"clients before={len(settings['clients'])}")

# 2. Add test client
test_uuid = str(uuid.uuid4())
settings['clients'].append({
    "id": test_uuid, "email": f"fin_test_{int(time.time())}",
    "enable": True, "expiryTime": int((time.time()+86400)*1000),
    "totalGB": 0, "flow": "xtls-rprx-vision", "limitIp": 0, "tgId": "", "subId": ""
})
obj['settings'] = settings

# 3. Update via correct URL
payload = {
    "id": obj['id'], "remark": obj.get('remark', ''), "enable": obj.get('enable', True),
    "listen": obj.get('listen', ''), "port": obj.get('port', 443),
    "protocol": obj.get('protocol', 'vless'), "tag": obj.get('tag', ''),
    "settings": obj['settings'],
    "streamSettings": obj.get('streamSettings', {}) if isinstance(obj.get('streamSettings'), dict) else (json.loads(obj.get('streamSettings', '{}')) if obj.get('streamSettings') else {}),
    "sniffing": obj.get('sniffing', {}) if isinstance(obj.get('sniffing'), dict) else (json.loads(obj.get('sniffing', '{}')) if obj.get('sniffing') else {}),
}
r2 = s.post(f'{host}/panel/api/inbounds/update/1', json=payload, headers=h)
print(f"update status={r2.status_code}")
try:
    print(f"update response={r2.json()}")
except:
    print(f"update body={r2.text[:200]!r}")

# 4. Verify
r3 = s.get(f'{host}/panel/api/inbounds/get/1', headers=h)
obj3 = r3.json()['obj']
raw3 = obj3.get('settings')
settings3 = raw3 if isinstance(raw3, dict) else (json.loads(raw3) if raw3 else {"clients": []})
print(f"clients after={len(settings3.get('clients', []))}")
for c in settings3.get('clients', []):
    if c.get('id') == test_uuid:
        print(f"FOUND test client: email={c['email']}")
        break
else:
    print("NOT found")

# 5. Cleanup
settings3['clients'] = [c for c in settings3.get('clients', []) if c.get('id') != test_uuid]
obj3['settings'] = settings3
payload3 = {
    "id": obj3['id'], "remark": obj3.get('remark', ''), "enable": obj3.get('enable', True),
    "listen": obj3.get('listen', ''), "port": obj3.get('port', 443),
    "protocol": obj3.get('protocol', 'vless'), "tag": obj3.get('tag', ''),
    "settings": obj3['settings'],
    "streamSettings": obj3.get('streamSettings', {}) if isinstance(obj3.get('streamSettings'), dict) else (json.loads(obj3.get('streamSettings', '{}')) if obj3.get('streamSettings') else {}),
    "sniffing": obj3.get('sniffing', {}) if isinstance(obj3.get('sniffing'), dict) else (json.loads(obj3.get('sniffing', '{}')) if obj3.get('sniffing') else {}),
}
r4 = s.post(f'{host}/panel/api/inbounds/update/1', json=payload3, headers=h)
print(f"cleanup status={r4.status_code}")
