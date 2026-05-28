#!/bin/bash
# Скрипт для восстановления всех активных peers из базы данных в WireGuard
# Используется при перезапуске сервера или бота

cd /root/vpn_bot

# Активация виртуального окружения
source vpn_env/bin/activate

# Установка переменных окружения (те же, что в start_bot.sh)
export SERVER_IP="90.156.169.27"
export SERVER_PUBLIC_KEY="LOn7s/VtqgAIWD9Ibu2rLoxC1zvcoIg+Ln7gx5LTB0Y="

# Запуск скрипта восстановления peers
python3 restore_peers.py

