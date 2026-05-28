import os, json, requests
from py3xui import Api
host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()
s = requests.Session(); s.verify = False; s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

# Получаем xray config
r = s.post(f'{host}/panel/api/xray/setting', headers=h)
print(f"status={r.status_code}")
try:
    data = r.json()
    print(f"success={data.get('success')}")
    obj = data.get('obj', {})
    if isinstance(obj, str):
        obj = json.loads(obj)
    
    # Проверяем outbounds
    outbounds = obj.get('outbounds', [])
    print(f"\nOutbounds count: {len(outbounds)}")
    for ob in outbounds:
        print(f"  - protocol={ob.get('protocol')}, tag={ob.get('tag')}")
        if ob.get('protocol') == 'freedom':
            print("    ✅ Freedom outbound найден")
    
    # Проверяем routing
    routing = obj.get('routing', {})
    rules = routing.get('rules', [])
    print(f"\nRouting rules: {len(rules)}")
    for rule in rules:
        print(f"  - {rule}")
        
except Exception as e:
    print(f"error: {e}")
    print(f"raw={r.text[:500]!r}")
