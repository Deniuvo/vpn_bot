import os, requests
from py3xui import Api
host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()
s = requests.Session(); s.verify = False; s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}
r = s.get(f'{host}/panel/api/inbounds/list', headers=h)
data = r.json()
print(f"success={data.get('success')}")
for ib in data.get('obj', []):
    print(f"id={ib.get('id')} remark={ib.get('remark')} port={ib.get('port')}")
