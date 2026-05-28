import sys, traceback
sys.path.insert(0, '/root/vpn_bot')

try:
    from cryptocloud_api import cryptocloud, create_cryptocloud_order_id
    print("IMPORT OK")
except Exception as e:
    print("IMPORT FAILED:", e)
    traceback.print_exc()
    exit(1)

try:
    result = cryptocloud.create_invoice(amount=1.33, order_id="vpn_test_123_1_month_999999", currency="USD")
    print("API RESULT:", result)
except Exception as e:
    print("API FAILED:", e)
    traceback.print_exc()
