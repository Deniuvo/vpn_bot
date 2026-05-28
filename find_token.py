import os
import glob

# Check environment
for k, v in os.environ.items():
    if 'YOOMONEY' in k.upper() or 'YMONEY' in k.upper() or 'ACCESS_TOKEN' in k.upper():
        print(f"ENV {k}={v[:50]}...")

# Check .env files
for path in ['/root/vpn_bot/.env', '/root/.env']:
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if 'YOOMONEY' in line.upper() or 'YMONEY' in line.upper() or 'TOKEN' in line.upper():
                    print(f"FILE {path}: {line.strip()[:80]}")

# Check token files
for pattern in ['/root/vpn_bot/*.token', '/root/*.token', '/root/vpn_bot/*token*']:
    for f in glob.glob(pattern):
        print(f"FOUND TOKEN FILE: {f}")
