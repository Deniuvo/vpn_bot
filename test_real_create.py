import os, json, time, uuid, requests
from py3xui import Api

host = os.getenv('XUI_HOST')
if not host:
    raise SystemExit("XUI_HOST не задан")

api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

inbound_id = os.getenv('XUI_INBOUND_ID', '2')

# Получаем inbound
r = s.get(f'{host}/panel/api/inbounds/get/{inbound_id}', headers=h)
data = r.json()
print(f"get inbound success={data.get('success')}")

if not data.get('success'):
    print(f"ERROR: {data.get('msg')}")
    exit(1)

obj = data['obj']
settings = obj.get('settings')
if isinstance(settings, str):
    settings = json.loads(settings)

clients = settings.get('clients', [])
print(f"clients before: {len(clients)}")

# Создаём нового клиента
test_uuid = str(uuid.uuid4())
new_client = {
    "id": test_uuid,
    "email": "test_client",
    "enable": True,
    "expiryTime": int((time.time() + 1 * 86400) * 1000),
    "totalGB": 0,
    "flow": "xtls-rprx-vision",
    "limitIp": 0,
    "tgId": "",
    "subId": "",
}
clients.append(new_client)

# Обновляем inbound
payload = {
    "id": obj.get("id"),
    "remark": obj.get("remark", ""),
    "enable": obj.get("enable", True),
    "listen": obj.get("listen", ""),
    "port": obj.get("port", 443),
    "protocol": obj.get("protocol", "vless"),
    "tag": obj.get("tag", ""),
    "settings": settings,
    "streamSettings": obj.get("streamSettings", {}),
    "sniffing": obj.get("sniffing", {}),
}

r = s.post(f'{host}/panel/api/inbounds/update/{inbound_id}', headers=h, json=payload)
print(f"update status={r.status_code}")
update_data = r.json()
print(f"update success={update_data.get('success')}, msg={update_data.get('msg')!r}")

if update_data.get('success'):
    # Проверяем, что клиент добавился
    r2 = s.get(f'{host}/panel/api/inbounds/get/{inbound_id}', headers=h)
    data2 = r2.json()
    obj2 = data2['obj']
    settings2 = obj2.get('settings')
    if isinstance(settings2, str):
        settings2 = json.loads(settings2)
    clients2 = settings2.get('clients', [])
    print(f"clients after: {len(clients2)}")
    
    # Находим нашего клиента
    for c in clients2:
        if c.get('id') == test_uuid:
            print(f"FOUND client: uuid={c.get('id')}, email={c.get('email')}")
            break
    else:
        print("WARNING: client not found after update!")
    
    # Удаляем тестового клиента
    clients2 = [c for c in clients2 if c.get('id') != test_uuid]
    payload['settings'] = settings2
    payload['id'] = obj2.get('id')
    r3 = s.post(f'{host}/panel/api/inbounds/update/{inbound_id}', headers=h, json=payload)
    print(f"cleanup status={r3.status_code}, success={r3.json().get('success')}")
else:
    print(f"ERROR updating: {r.text[:300]}")
