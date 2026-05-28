#!/usr/bin/env python3
"""
Получение access_token для API ЮMoney через OAuth2
Запустите на сервере и следуйте инструкциям
"""
import urllib.parse
import requests

CLIENT_ID = "9BC961BE2FCB3D6A07320B85144EE045C4C73618A78A617C27EC0894397DC61F"
CLIENT_SECRET = "14ECCC895A41D72C733363E6EC2FEC601C53957DACC007EB39A5B093D9500EDB905FEE99134673BA7076F1FCA75A0DA0F97E879112B72FDAA812EC188402869D"
REDIRECT_URI = "https://yoomoney.ru"
SCOPE = "account-info operation-history"

# Step 1: Build authorization URL
params = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
}
auth_url = "https://yoomoney.ru/oauth/authorize?" + urllib.parse.urlencode(params)

print("=" * 60)
print("ПОЛУЧЕНИЕ ACCESS TOKEN ДЛЮ ЮMONEY API")
print("=" * 60)
print()
print("1. Откройте эту ссылку в браузере (где вы залогинены в ЮMoney):")
print()
print(auth_url)
print()
print("2. Авторизуйте приложение 'CloudHapp'")
print("3. Браузер перенаправит на https://yoomoney.ru?code=XXXX")
print("4. Скопируйте значение 'code' из URL")
print()

code = input("Введите code: ").strip()
if not code:
    print("ERROR: code не введен")
    exit(1)

# Step 2: Exchange code for token
print()
print("Обмениваю code на access_token...")

token_data = {
    "grant_type": "authorization_code",
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
}

resp = requests.post("https://yoomoney.ru/oauth/token", data=token_data, timeout=30)
print(f"HTTP {resp.status_code}")

if resp.status_code == 200:
    result = resp.json()
    access_token = result.get("access_token")
    if access_token:
        print()
        print("=" * 60)
        print("SUCCESS! Access token получен:")
        print("=" * 60)
        print(f"access_token = {access_token}")
        print()
        print("Добавьте в /root/vpn_bot/.env строку:")
        print(f'YMONEY_ACCESS_TOKEN={access_token}')
        print()
        print("Или выполните:")
        print(f'echo "YMONEY_ACCESS_TOKEN={access_token}" >> /root/vpn_bot/.env')
        print()
        
        # Auto-save to .env
        env_path = "/root/vpn_bot/.env"
        try:
            with open(env_path, "a") as f:
                f.write(f"\nYMONEY_ACCESS_TOKEN={access_token}\n")
            print(f"Token автоматически сохранен в {env_path}")
        except Exception as e:
            print(f"Не удалось сохранить автоматически: {e}")
    else:
        print("ERROR: access_token не найден в ответе")
        print(resp.text)
else:
    print("ERROR:")
    print(resp.text)
