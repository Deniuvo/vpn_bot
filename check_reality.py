import os, json, requests
from py3xui import Api
host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()
s = requests.Session(); s.verify = False; s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}
r = s.get(f'{host}/panel/api/inbounds/get/2', headers=h)
obj = r.json()['obj']
ss = obj.get('streamSettings')
if isinstance(ss, str): ss = json.loads(ss)
rs = ss.get('realitySettings', {})
print(json.dumps(rs, indent=2))
