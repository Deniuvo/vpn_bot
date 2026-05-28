#!/bin/bash
# Скрипт автоматической установки и настройки Shadowsocks для обфускации WireGuard

set -e

echo "🔧 Установка и настройка Shadowsocks..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Установка Shadowsocks
echo -e "${YELLOW}1. Установка Shadowsocks...${NC}"
sudo apt update
sudo apt install -y shadowsocks-libev simple-obfs

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Shadowsocks установлен${NC}"
else
    echo -e "${RED}❌ Ошибка установки Shadowsocks${NC}"
    exit 1
fi

# 2. Создание директории для конфига (если не существует)
echo -e "${YELLOW}2. Создание директории для конфига...${NC}"
sudo mkdir -p /etc/shadowsocks-libev

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Директория создана${NC}"
else
    echo -e "${RED}❌ Ошибка создания директории${NC}"
    exit 1
fi

# 3. Генерация пароля
echo -e "${YELLOW}3. Генерация пароля...${NC}"
PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo -e "${GREEN}✅ Пароль сгенерирован${NC}"
echo -e "${YELLOW}📝 Сохраните этот пароль: ${PASSWORD}${NC}"

# 4. Создание конфига
echo -e "${YELLOW}4. Создание конфигурационного файла...${NC}"

# Определяем основной сетевой интерфейс
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)
if [ -z "$MAIN_INTERFACE" ]; then
    MAIN_INTERFACE="eth0"
fi

# Создаем временный файл конфига
TEMP_CONFIG=$(mktemp)
cat > "$TEMP_CONFIG" << EOF
{
    "server": "0.0.0.0",
    "server_port": 8388,
    "local_address": "127.0.0.1",
    "local_port": 51820,
    "password": "${PASSWORD}",
    "timeout": 300,
    "method": "chacha20-ietf-poly1305",
    "fast_open": true,
    "mode": "tcp_and_udp",
    "plugin": "obfs-server",
    "plugin_opts": "obfs=http"
}
EOF

# Копируем конфиг с правами root
sudo cp "$TEMP_CONFIG" /etc/shadowsocks-libev/config.json
sudo chmod 600 /etc/shadowsocks-libev/config.json
rm "$TEMP_CONFIG"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Конфиг создан: /etc/shadowsocks-libev/config.json${NC}"
else
    echo -e "${RED}❌ Ошибка создания конфига${NC}"
    exit 1
fi

# 5. Настройка файрвола
echo -e "${YELLOW}5. Настройка файрвола...${NC}"

# Проверяем UFW
if command -v ufw &> /dev/null; then
    sudo ufw allow 8388/tcp
    sudo ufw allow 8388/udp
    echo -e "${GREEN}✅ Порты открыты в UFW${NC}"
fi

# Проверяем iptables
if command -v iptables &> /dev/null; then
    sudo iptables -A INPUT -p tcp --dport 8388 -j ACCEPT 2>/dev/null || true
    sudo iptables -A INPUT -p udp --dport 8388 -j ACCEPT 2>/dev/null || true
    echo -e "${GREEN}✅ Порты открыты в iptables${NC}"
fi

# 6. Запуск Shadowsocks
echo -e "${YELLOW}6. Запуск Shadowsocks...${NC}"
sudo systemctl enable shadowsocks-libev
sudo systemctl restart shadowsocks-libev

# Проверка статуса
sleep 2
if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска Shadowsocks${NC}"
    echo -e "${YELLOW}Проверьте логи: sudo journalctl -u shadowsocks-libev -n 50${NC}"
    exit 1
fi

# 7. Вывод информации
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Shadowsocks успешно настроен!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📋 Параметры подключения:"
echo "   Сервер: $(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"
echo "   Порт: 8388"
echo "   Метод: chacha20-ietf-poly1305"
echo "   Пароль: ${PASSWORD}"
echo "   Плагин: obfs-server"
echo "   Опции плагина: obfs=http"
echo ""
echo "⚠️  ВАЖНО: Сохраните пароль!"
echo ""
echo "📝 Проверка статуса:"
echo "   sudo systemctl status shadowsocks-libev"
echo ""
echo "📝 Просмотр логов:"
echo "   sudo journalctl -u shadowsocks-libev -f"
echo ""
echo "📝 Редактирование конфига:"
echo "   sudo nano /etc/shadowsocks-libev/config.json"
echo ""
echo "🔄 Перезапуск:"
echo "   sudo systemctl restart shadowsocks-libev"
echo ""

