#!/bin/bash
cd /root/vpn_bot

echo "Creating venv..."
python3 -m venv venv
echo "Installing packages..."
venv/bin/pip install -q -r requirements.txt
echo "Done."

pkill -f bot.py 2>/dev/null
sleep 1
source /root/vpn_bot/set_env_vars.sh
nohup venv/bin/python bot.py > /root/vpn_bot/vpn_bot.log 2>&1 &
echo "Bot started, PID=$!"
sleep 4
tail -15 /root/vpn_bot/vpn_bot.log
