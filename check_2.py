import os, json, requests
from py3xui import Api
host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()
s = requests.Session(); s.verify = False; s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}
r = s.get(f'{host}/panel/api/inbounds/get/2', headers=h)
data = r.json()
print(f"success={data.get('success')}, msg={data.get('msg')!r}")
obj = data.get('obj', {})
print(f"keys={list(obj.keys())}")
print(f"port={obj.get('port')}, protocol={obj.get('protocol')}, remark={obj.get('remark')}")

ss = obj.get('streamSettings')
if isinstance(ss, str): ss = json.loads(ss)
rs = ss.get('realitySettings', {}) if ss else {}
print(f"serverNames={rs.get('serverNames')}")
print(f"publicKey={rs.get('publicKey')}")
print(f"shortIds={rs.get('shortIds')}")

settings = obj.get('settings')
if isinstance(settings, str): settings = json.loads(settings)
print(f"clients count={len(settings.get('clients', [])) if settings else 0}")
