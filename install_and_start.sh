#!/bin/bash
echo "Installing dependencies..."
pip3 install -r /root/vpn_bot/requirements.txt -q
echo "Done. Starting bot..."
pkill -f bot.py 2>/dev/null
sleep 1
source /root/vpn_bot/set_env_vars.sh
nohup python3 /root/vpn_bot/bot.py > /root/vpn_bot/vpn_bot.log 2>&1 &
echo "Bot started, PID=$!"
sleep 4
tail -15 /root/vpn_bot/vpn_bot.log
