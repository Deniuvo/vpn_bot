import os, requests
from py3xui import Api

host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': api._session})
headers = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

urls = [
    '/panel/api/inbounds/update',
    '/panel/api/inbounds/update/1',
    '/panel/api/inbounds/updateInbound',
    '/panel/api/inbounds/updateInbound/1',
    '/panel/api/inbounds/1/update',
    '/panel/api/inbounds/1',
    '/panel/api/inbounds/save',
    '/panel/api/inbounds/save/1',
    '/panel/inbound/update',
    '/panel/inbound/update/1',
    '/panel/api/inbound/update',
    '/panel/api/inbound/update/1',
]
for u in urls:
    r = s.post(f'{host}{u}', json={'id': 1, 'remark': 'test'}, headers=headers)
    print(f'{r.status_code:3d} {u}')
