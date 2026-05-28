import subprocess
result = subprocess.run(['journalctl', '-u', 'vpn-bot', '--no-pager', '-n', '50'], capture_output=True, text=True)
lines = result.stdout.split('\n')
for line in lines:
    if 'buy' in line.lower() or 'show_tariffs' in line.lower() or 'tariff' in line.lower():
        print(line)
