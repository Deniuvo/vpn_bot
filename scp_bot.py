import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('85.234.106.239', username='root', password='vuw,K96s,qVeBt', timeout=10)
    sftp = ssh.open_sftp()
    sftp.put('C:/Users/1/Desktop/vpn_bot/bot.py', '/root/vpn_bot/bot.py')
    sftp.close()
    ssh.close()
    print('SCP OK')
except Exception as e:
    print(f'ERROR: {e}')
