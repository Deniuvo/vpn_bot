with open('/root/vpn_bot/database.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[19:99], start=20):
        print(f"{i}: {line}", end="")
