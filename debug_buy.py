import sys
sys.path.insert(0, '/root/vpn_bot')
from bot import buy_command, show_tariffs, TARIFFS, WAITING_PAYMENT
print("buy_command defined:", buy_command is not None)
print("show_tariffs defined:", show_tariffs is not None)
print("TARIFFS:", list(TARIFFS.keys()))
print("WAITING_PAYMENT:", WAITING_PAYMENT)
