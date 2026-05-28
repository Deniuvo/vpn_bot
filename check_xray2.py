import os, json, requests
from py3xui import Api
host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()
s = requests.Session(); s.verify = False; s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

urls = [
    '/xui/setting/xray',
    '/panel/setting/xray',
    '/panel/xray/setting',
    '/xray/setting',
    '/panel/api/xray/setting',
]

for u in urls:
    r = s.get(f'{host}{u}', headers=h)
    print(f"{u}: status={r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"  success={data.get('success')}")
            if data.get('obj'):
                print(f"  HAS DATA")
                break
        except:
            print(f"  not json: {r.text[:100]!r}")
