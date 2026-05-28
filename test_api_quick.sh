#!/bin/bash
# Быстрая проверка API с новым токеном
export YMONEY_ACCESS_TOKEN="4100119393589473.0AD0F449E8D86154FE467FEF584706F9B4ED5826CE35F14180ED80472F99A38861F4B7CCE722E8BFC1BBC5A9AB579D16953D31BB70B172B81FDB12DED211E570A05ACEA172A8279C82DCFECB7ED1AA3B311D5D77037BDA84D3AA539CEF85907E9F5E4B5FE8702EC1CD869EB7D4504F542BA77EC51578818D672EE7977E29BE00"

python3 -c "
import requests
from datetime import datetime, timedelta

token = '$YMONEY_ACCESS_TOKEN'
headers = {'Authorization': f'Bearer {token}'}

print('=== account-info ===')
r = requests.post('https://yoomoney.ru/api/account-info', headers=headers)
print(f'Статус: {r.status_code}')
print(f'Ответ: {r.text[:300]}')
print()

print('=== operation-history ===')
params = {'type': 'deposition', 'records': 10}
r = requests.post('https://yoomoney.ru/api/operation-history', headers=headers, data=params)
print(f'Статус: {r.status_code}')
print(f'Ответ: {r.text[:500]}')
"
