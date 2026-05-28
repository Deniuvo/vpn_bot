import sys
sys.path.insert(0, '/root/vpn_bot')
import os

# Read values from bot.py context
with open('/root/vpn_bot/bot.py', 'r') as f:
    content = f.read()
    
# Extract values
for line in content.split('\n'):
    if 'USE_YOOMONEY_API' in line and '=' in line and 'os.getenv' in line:
        print('USE_YOOMONEY_API line:', line.strip())
    if 'YMONEY_ACCESS_TOKEN' in line and '=' in line:
        print('YMONEY_ACCESS_TOKEN line:', line.strip())
    if 'YOOMONEY_CLIENT_ID' in line and '=' in line and 'os.getenv' in line:
        print('CLIENT_ID line:', line.strip())

print('---')
print('Env USE_YOOMONEY_API:', os.getenv('USE_YOOMONEY_API', 'NOT SET'))
print('Env YMONEY_ACCESS_TOKEN:', 'SET' if os.getenv('YMONEY_ACCESS_TOKEN') else 'NOT SET')
print('Env YOOMONEY_CLIENT_ID:', os.getenv('YOOMONEY_CLIENT_ID', 'NOT SET'))
