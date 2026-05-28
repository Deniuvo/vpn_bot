import os, json, requests
from py3xui import Api

host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

r = s.get(f'{host}/panel/api/inbounds/get/1', headers=h)
print(f"status={r.status_code}")
data = r.json()
print(f"success={data.get('success')}")
print(f"msg={data.get('msg')!r}")
print(f"obj_type={type(data.get('obj')).__name__}")
if data.get('obj'):
    obj = data['obj']
    print(f"keys={list(obj.keys())}")
    
    ss = obj.get('streamSettings')
    print(f"streamSettings_type={type(ss).__name__}")
    if ss is None:
        ss = {}
    elif isinstance(ss, str):
        ss = json.loads(ss)
    
    rs = ss.get('realitySettings', {})
    print(f"realitySettings keys={list(rs.keys()) if rs else 'empty'}")
    print(f"serverNames={rs.get('serverNames')}")
    print(f"shortIds={rs.get('shortIds')}")
    print(f"publicKey={rs.get('publicKey')}")
    if not rs.get('publicKey') and rs.get('privateKey'):
        print("No publicKey but has privateKey — need to compute")
else:
    print(f"raw={r.text[:500]!r}")
