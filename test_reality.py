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
obj = r.json()['obj']

ss = obj.get('streamSettings', {})
if isinstance(ss, str):
    ss = json.loads(ss)

rs = ss.get('realitySettings', {})
print(f"serverNames={rs.get('serverNames')}")
print(f"publicKey={rs.get('publicKey')}")
print(f"shortIds={rs.get('shortIds')}")
print(f"privateKey exists={'privateKey' in rs}")
print(f"show={rs.get('show')}")
print(f"xver={rs.get('xver')}")
print(f"target={rs.get('target')}")
