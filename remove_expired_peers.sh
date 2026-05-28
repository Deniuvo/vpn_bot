#!/bin/bash
# Скрипт для удаления истекших подписок с WireGuard сервера
# Устанавливает переменные окружения и запускает Python скрипт

cd /root/vpn_bot

# Активация виртуального окружения
source vpn_env/bin/activate

# Установка переменных окружения (те же, что в start_bot.sh)
export SERVER_IP="90.156.169.27"
export SERVER_PUBLIC_KEY="LOn7s/VtqgAIWD9Ibu2rLoxC1zvcoIg+Ln7gx5LTB0Y="

# Запуск скрипта удаления истекших подписок
python3 remove_expired_peers.py

