import os, json, uuid, time, requests, inspect
from py3xui import Api, Client

host = os.getenv("XUI_HOST", "http://localhost:44875/3wBsYxDX2cUOynnPcl")
user = os.getenv("XUI_USERNAME", "root")
password = os.getenv("XUI_PASSWORD", "")
iid  = int(os.getenv("XUI_INBOUND_ID", "1"))

print(f"Host: {host}")
print(f"User: {user!r}, pass_len={len(password)}")

# --- py3xui introspection ---
print("\n=== py3xui Api introspection ===")
api = Api(host, user, password, use_tls_verify=False)
print(f"Api type: {type(api).__name__}")
print(f"Api module: {type(api).__module__}")

for name in sorted(dir(api)):
    if name.startswith('__') and name.endswith('__'):
        continue
    try:
        val = getattr(api, name)
        if callable(val):
            print(f"  METHOD: {name}()")
        else:
            print(f"  ATTR: {name} = {type(val).__name__}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

# --- Login ---
print("\n=== py3xui login ===")
try:
    api.login()
    print("OK: logged in")
except Exception as e:
    print(f"FAIL: {e}")

# --- After-login introspection ---
print("\n=== After-login attributes ===")
for name in sorted(dir(api)):
    if any(k in name.lower() for k in ['session', 'cookie', 'http', 'client', 'conn', 'auth', 'token']):
        try:
            val = getattr(api, name)
            t = type(val).__name__
            print(f"  {name}: type={t}")
            if hasattr(val, 'cookies'):
                print(f"    cookies={dict(val.cookies)}")
            if hasattr(val, 'headers'):
                print(f"    headers={dict(val.headers)}")
            if not callable(val) and t not in ('str','int','bool','float','NoneType','list','dict'):
                print(f"    repr={repr(val)[:300]}")
        except Exception as e:
            print(f"  {name}: ERROR {e}")

# --- Test direct requests with various formats ---
print("\n=== Direct request tests ===")
tests = [
    ("json", {"json": {"username": user, "password": password}}),
    ("json+Accept", {"json": {"username": user, "password": password}, "headers": {"Accept": "application/json"}}),
    ("data", {"data": {"username": user, "password": password}}),
    ("data+Accept", {"data": {"username": user, "password": password}, "headers": {"Accept": "application/json"}}),
    ("data+urlencoded", {"data": {"username": user, "password": password}, "headers": {"Content-Type": "application/x-www-form-urlencoded"}}),
    ("multipart", {"files": {"username": (None, user), "password": (None, password)}}),
]

for name, kwargs in tests:
    s = requests.Session()
    s.verify = False
    r = s.post(f"{host}/login", **kwargs)
    print(f"  {name}: status={r.status_code}, body={r.text[:120]!r}")

# --- Test if py3xui has inbound/client methods ---
print("\n=== py3xui methods test ===")
for method_name in ['get_inbounds', 'get_inbound', 'add_client', 'client_add', 
                     'del_client', 'client_del', 'update_client', 'client_update',
                     'get_clients', 'get_client']:
    if hasattr(api, method_name):
        print(f"  HAS: {method_name}")
    else:
        print(f"  missing: {method_name}")
