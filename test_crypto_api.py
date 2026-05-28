import sys
sys.path.insert(0, '/root/vpn_bot')
from cryptocloud_api import cryptocloud

result = cryptocloud.create_invoice(
    amount=1.33,
    order_id="vpn_test_123_1_month_999999",
    currency="USD"
)
print("RESULT:", result)
