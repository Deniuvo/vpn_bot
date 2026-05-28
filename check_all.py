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

print("=== ALL realitySettings keys ===")
for k, v in rs.items():
    t = type(v).__name__
    if k in ['privateKey', 'publicKey'] and isinstance(v, str):
        print(f"{k}={v[:20]}... (len={len(v)})")
    elif isinstance(v, list):
        print(f"{k}={v[:3]}...")
    else:
        print(f"{k}={v}")

# Check if privateKey exists
priv = rs.get('privateKey')
if priv:
    print(f"\nFound privateKey! Computing publicKey...")
    try:
        import base64
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        priv_bytes = base64.b64decode(priv)
        private_key = X25519PrivateKey.from_private_bytes(priv_bytes)
        pub_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        pub_b64 = base64.b64encode(pub_bytes).decode()
        print(f"computed publicKey={pub_b64}")
    except Exception as e:
        print(f"compute error: {e}")
else:
    print("\nNo privateKey found")
