#!/bin/bash
# Простой скрипт для быстрой установки через SSH
# Использование: bash deploy_simple.sh user@server

if [ -z "$1" ]; then
    echo "Использование: bash deploy_simple.sh user@server"
    echo "Пример: bash deploy_simple.sh root@192.168.1.100"
    exit 1
fi

SERVER=$1
SSH_CMD="ssh -o StrictHostKeyChecking=no"

echo "🚀 Установка VPN бота на $SERVER"
echo "=================================="

# Проверка подключения
echo "🔌 Проверка подключения..."
$SSH_CMD $SERVER 'echo "Подключено успешно"' || {
    echo "❌ Не удалось подключиться. Проверьте SSH ключи или пароль."
    exit 1
}

echo ""
echo "📦 Установка зависимостей Python..."
$SSH_CMD $SERVER 'cd /root/vpn_bot && python3 -m venv vpn_env && source vpn_env/bin/activate && pip install --upgrade pip --quiet && pip install -r requirements.txt'

echo ""
echo "🔐 Установка WireGuard..."
$SSH_CMD $SERVER 'cd /root/vpn_bot && sudo bash setup_wireguard.sh'

echo ""
echo "📋 Получение данных сервера..."
$SSH_CMD $SERVER 'cd /root/vpn_bot && source vpn_env/bin/activate && python3 setup_server.py'

echo ""
echo "⚙️  Настройка переменных окружения..."

# Получаем данные
PUBLIC_IP=$($SSH_CMD $SERVER 'curl -s ifconfig.me || curl -s ipinfo.io/ip')
WG_KEY=$($SSH_CMD $SERVER 'sudo wg show wg0 public-key 2>/dev/null || echo ""')
YMONEY_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"

# Устанавливаем переменные
$SSH_CMD $SERVER "echo 'export SERVER_IP=\"$PUBLIC_IP\"' >> ~/.bashrc"
$SSH_CMD $SERVER "echo 'export SERVER_PUBLIC_KEY=\"$WG_KEY\"' >> ~/.bashrc"
$SSH_CMD $SERVER "echo 'export YMONEY_ACCESS_TOKEN=\"$YMONEY_TOKEN\"' >> ~/.bashrc"
$SSH_CMD $SERVER "echo 'export USE_YOOMONEY_API=\"true\"' >> ~/.bashrc"

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Данные сервера:"
echo "   SERVER_IP: $PUBLIC_IP"
echo "   SERVER_PUBLIC_KEY: $WG_KEY"
echo ""
echo "🚀 Запуск бота:"
echo "   ssh $SERVER"
echo "   cd /root/vpn_bot"
echo "   source vpn_env/bin/activate"
echo "   python3 main.py"

