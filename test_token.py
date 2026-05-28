import requests

# Read token from .env
with open('/root/vpn_bot/.env') as f:
    token = None
    for line in f:
        if line.startswith('YMONEY_ACCESS_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

if not token:
    print("NO TOKEN")
    exit(1)

print(f"Token: {token[:30]}...")

# Test API
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}
resp = requests.post("https://yoomoney.ru/api/account-info", headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text[:500]}")
