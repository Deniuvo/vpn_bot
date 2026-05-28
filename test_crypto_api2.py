import sys, json
sys.path.insert(0, '/root/vpn_bot')
from cryptocloud_api import cryptocloud

result = cryptocloud.create_invoice(
    amount=1.33,
    order_id="vpn_test_123_1_month_999999",
    currency="USD"
)
print("TYPE:", type(result))
print("KEYS:", list(result.keys()) if result else "NONE")
if result:
    print("link:", result.get('link'))
    print("uuid:", result.get('uuid'))
    print("status:", result.get('status'))
    print(json.dumps(result, indent=2, default=str)[:800])
