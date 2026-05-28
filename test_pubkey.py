import os, json, base64, requests
from py3xui import Api

host = os.getenv('XUI_HOST')
api = Api(host, os.getenv('XUI_USERNAME'), os.getenv('XUI_PASSWORD'), use_tls_verify=False)
api.login()

s = requests.Session()
s.verify = False
s.cookies.update({'3x-ui': api._session})
h = {'Accept': 'application/json', 'X-CSRF-Token': api._csrf_token}

r = s.get(f'{host}/panel/api/inbounds/get/1', headers=h)
data = r.json()
obj = data.get('obj', {})

print(f"success={data.get('success')}")
print(f"keys={list(obj.keys())}")

ss = obj.get('streamSettings')
if ss is None:
    print("streamSettings=None")
    ss = {}
elif isinstance(ss, str):
    ss = json.loads(ss)

rs = ss.get('realitySettings', {})
print(f"serverNames={rs.get('serverNames')}")
print(f"shortIds={rs.get('shortIds')}")

priv = rs.get('privateKey')
if priv:
    print(f"privateKey={priv[:30]}...")
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        priv_bytes = base64.b64decode(priv)
        private_key = X25519PrivateKey.from_private_bytes(priv_bytes)
        pub_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        pub_b64 = base64.b64encode(pub_bytes).decode()
        print(f"publicKey={pub_b64}")
    except Exception as e:
        print(f"compute error: {e}")
else:
    print("privateKey not found")
