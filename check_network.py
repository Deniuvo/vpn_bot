import socket, ssl

# Проверяем DNS
for host in ['instagram.com', 'telegram.org', 'google.com']:
    try:
        ip = socket.getaddrinfo(host, None)[0][4][0]
        print(f"{host} -> {ip}")
    except Exception as e:
        print(f"{host} -> ERROR: {e}")

# Проверяем SSL
for ip in ['31.13.71.174', '149.154.167.99']:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((ip, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname='instagram.com') as ssock:
                print(f"SSL {ip}: OK")
    except Exception as e:
        print(f"SSL {ip}: {e}")
