#!/bin/bash
# Скрипт запуска VPN бота с установкой переменных окружения

cd /root/vpn_bot

# Активация виртуального окружения
source vpn_env/bin/activate

# Установка переменных окружения
export SERVER_IP="90.156.169.27"
export SERVER_PUBLIC_KEY="LOn7s/VtqgAIWD9Ibu2rLoxC1zvcoIg+Ln7gx5LTB0Y="
# Токен приложения «CloudHapp» (см. yoomoney_token.txt или get_yoomoney_token.sh)
export YMONEY_ACCESS_TOKEN="4100119393589473.AE7076BAC913832A79D260C77D94EBD7B10637FCDA32D42340903473AE8B1B371D18FBD438CCE3A8031A65EE74C9D69D4D32343F7DAF0DBB407C09E440E1742D56597912415DD5C7E0D26A3673A7B6C14D4DB41ABD113E405E62C97E88327346BAB68015F71DE47051036440595085912DF9A54DE4A96060951C36B383335CA9"
export USE_YOOMONEY_API="true"

# Запуск бота
nohup python3 main.py > vpn.log 2>&1 &

echo "✅ VPN бот запущен! PID: $!"
echo "📋 Логи: tail -f /root/vpn_bot/vpn.log"


