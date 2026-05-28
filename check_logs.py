import subprocess
import sys
sys.path.insert(0, '/root/vpn_bot')

# Check recent logs for crypto-related errors
result = subprocess.run(['journalctl', '-u', 'vpn-bot', '--no-pager', '-n', '30'], capture_output=True, text=True)
lines = result.stdout.split('\n')
for line in lines[-15:]:
    if 'crypto' in line.lower() or 'error' in line.lower() or 'CryptoCloud' in line:
        print(line)
