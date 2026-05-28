import requests
import sys

CLIENT_ID = "9BC961BE2FCB3D6A07320B85144EE045C4C73618A78A617C27EC0894397DC61F"
CLIENT_SECRET = "14ECCC895A41D72C733363E6EC2FEC601C53957DACC007EB39A5B093D9500EDB905FEE99134673BA7076F1FCA75A0DA0F97E879112B72FDAA812EC188402869D"
REDIRECT_URI = "https://yoomoney.ru"

code = sys.argv[1] if len(sys.argv) > 1 else input("code: ").strip()

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
        print(f"ACCESS_TOKEN={access_token}")
        with open("/root/vpn_bot/.env", "a") as f:
            f.write(f"\nYMONEY_ACCESS_TOKEN={access_token}\n")
        print("Token saved to /root/vpn_bot/.env")
    else:
        print("ERROR: no access_token")
        print(result)
else:
    print("ERROR:", resp.text)
