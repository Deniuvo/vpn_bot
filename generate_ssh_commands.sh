#!/bin/bash
# Генератор команд для копирования и выполнения на сервере
# Создает файл со всеми командами для ручного выполнения

OUTPUT_FILE="ssh_commands.txt"

cat > "$OUTPUT_FILE" << 'EOF'
# ============================================================
# Команды для установки VPN бота на сервере
# Скопируйте и выполните эти команды на вашем сервере
# ============================================================

# 1. Переход в директорию проекта
cd /root/vpn_bot

# 2. Создание виртуального окружения Python
python3 -m venv vpn_env
source vpn_env/bin/activate

# 3. Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# 4. Установка и настройка WireGuard (автоматически с защитой SSH)
sudo bash setup_wireguard.sh

# 5. Получение данных сервера
python3 setup_server.py

# 6. Установка переменных окружения
# Получите значения автоматически:
SERVER_IP=\$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
SERVER_PUBLIC_KEY=\$(sudo wg show wg0 public-key || sudo cat /etc/wireguard/public.key)
YMONEY_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"

export SERVER_IP="\$SERVER_IP"
export SERVER_PUBLIC_KEY="\$SERVER_PUBLIC_KEY"
export YMONEY_ACCESS_TOKEN="\$YMONEY_TOKEN"
export USE_YOOMONEY_API="true"

# 7. Для постоянного сохранения переменных
echo "export SERVER_IP=\"\$SERVER_IP\"" >> ~/.bashrc
echo "export SERVER_PUBLIC_KEY=\"\$SERVER_PUBLIC_KEY\"" >> ~/.bashrc
echo "export YMONEY_ACCESS_TOKEN=\"\$YMONEY_TOKEN\"" >> ~/.bashrc
echo "export USE_YOOMONEY_API=\"true\"" >> ~/.bashrc
source ~/.bashrc

# 8. Проверка настроек
echo "SERVER_IP: $SERVER_IP"
echo "SERVER_PUBLIC_KEY: $SERVER_PUBLIC_KEY"
sudo wg show

# 9. Запуск бота
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py

# ============================================================
# Готово! Бот должен быть запущен.
# Для запуска в фоне используйте screen или systemd (см. DEPLOY.md)
# ============================================================
EOF

echo "✅ Файл с командами создан: $OUTPUT_FILE"
echo ""
echo "📋 Использование:"
echo "   1. Откройте файл $OUTPUT_FILE"
echo "   2. Скопируйте команды"
echo "   3. Вставьте в SSH консоль сервера"
echo ""

