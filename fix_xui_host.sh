#!/bin/bash
python3 -c "
f='/root/vpn_bot/set_env_vars.sh'
t=open(f).read().replace('http://localhost:2053','http://localhost:44875/3wBsYxDX2cUOynnPcl')
open(f,'w').write(t)
"
echo "XUI_HOST updated:"
grep XUI_HOST /root/vpn_bot/set_env_vars.sh

pkill -f bot.py 2>/dev/null
sleep 1
source /root/vpn_bot/set_env_vars.sh
nohup python3 /root/vpn_bot/bot.py > /root/vpn_bot/vpn_bot.log 2>&1 &
echo "Bot started, PID=$!"
sleep 3
tail -10 /root/vpn_bot/vpn_bot.log
