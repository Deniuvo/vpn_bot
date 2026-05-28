#!/bin/bash
# Финальное исправление Shadowsocks - правильная настройка systemd

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔧 Финальное исправление Shadowsocks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Проверка установки
echo -e "${YELLOW}[1/7] Проверка установки...${NC}"
if ! command -v ss-server &> /dev/null; then
    echo -e "${RED}❌ ss-server не найден!${NC}"
    echo -e "${YELLOW}Устанавливаю Shadowsocks...${NC}"
    sudo apt update
    sudo apt install -y shadowsocks-libev
fi

SS_SERVER=$(which ss-server || echo "/usr/bin/ss-server")
echo -e "${GREEN}✅ ss-server найден: $SS_SERVER${NC}"
echo ""

# 2. Проверка конфига
echo -e "${YELLOW}[2/7] Проверка конфига...${NC}"
CONFIG_PATH="/etc/shadowsocks-libev/config.json"

if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}❌ Конфиг не найден! Создаю...${NC}"
    sudo mkdir -p /etc/shadowsocks-libev
    PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    sudo bash -c "cat > $CONFIG_PATH << 'EOF'
{
    \"server\": \"0.0.0.0\",
    \"server_port\": 8388,
    \"local_address\": \"127.0.0.1\",
    \"local_port\": 51820,
    \"password\": \"${PASSWORD}\",
    \"timeout\": 300,
    \"method\": \"chacha20-ietf-poly1305\",
    \"fast_open\": true,
    \"mode\": \"tcp_and_udp\"
}
EOF"
    echo -e "${GREEN}✅ Конфиг создан${NC}"
else
    echo -e "${GREEN}✅ Конфиг существует${NC}"
fi

# Проверка прав
sudo chmod 600 "$CONFIG_PATH"
sudo chown root:root "$CONFIG_PATH" 2>/dev/null || true
echo -e "${GREEN}✅ Права установлены${NC}"
echo ""

# 3. Проверка синтаксиса конфига
echo -e "${YELLOW}[3/7] Проверка синтаксиса конфига...${NC}"
if $SS_SERVER -c "$CONFIG_PATH" -t 2>&1 | grep -q "error"; then
    echo -e "${RED}❌ Ошибка в синтаксисе!${NC}"
    $SS_SERVER -c "$CONFIG_PATH" -t
    exit 1
else
    echo -e "${GREEN}✅ Синтаксис правильный${NC}"
fi
echo ""

# 4. Тестовый запуск вручную
echo -e "${YELLOW}[4/7] Тестовый запуск...${NC}"
sudo systemctl stop shadowsocks-libev 2>/dev/null || true
sleep 1

# Пробуем запустить вручную
if timeout 3 sudo $SS_SERVER -c "$CONFIG_PATH" -u -v 2>&1 | head -n 5; then
    echo -e "${GREEN}✅ Ручной запуск работает${NC}"
else
    echo -e "${YELLOW}⚠️ Ручной запуск не показал ошибок${NC}"
fi
echo ""

# 5. Создание правильного override для systemd
echo -e "${YELLOW}[5/7] Создание systemd override...${NC}"
sudo mkdir -p /etc/systemd/system/shadowsocks-libev.service.d/

# Получаем абсолютный путь к ss-server
SS_SERVER_ABS=$(readlink -f "$SS_SERVER" || echo "$SS_SERVER")

sudo bash -c "cat > /etc/systemd/system/shadowsocks-libev.service.d/override.conf << 'OVERRIDE_EOF'
[Service]
ExecStart=
ExecStart=$SS_SERVER_ABS -c $CONFIG_PATH -u
StandardOutput=journal
StandardError=journal
OVERRIDE_EOF"

echo -e "${GREEN}✅ Override создан${NC}"
echo ""
echo "Содержимое override:"
cat /etc/systemd/system/shadowsocks-libev.service.d/override.conf
echo ""

# 6. Перезагрузка systemd
echo -e "${YELLOW}[6/7] Перезагрузка systemd...${NC}"
sudo systemctl daemon-reload
echo -e "${GREEN}✅ systemd перезагружен${NC}"
echo ""

# 7. Запуск сервиса
echo -e "${YELLOW}[7/7] Запуск сервиса...${NC}"
sudo systemctl enable shadowsocks-libev
sudo systemctl restart shadowsocks-libev

# Ждем запуска
sleep 4

# Проверка статуса
if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks успешно запущен!${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 Успешно настроен!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Показываем статус
    sudo systemctl status shadowsocks-libev --no-pager -l | head -n 15
    echo ""
    
    # Показываем информацию о подключении
    if [ -f "$CONFIG_PATH" ]; then
        PASSWORD=$(grep -o '"password": "[^"]*"' "$CONFIG_PATH" | cut -d'"' -f4)
        SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
        echo -e "${YELLOW}📋 Информация о подключении:${NC}"
        echo -e "   ${BLUE}Сервер:${NC} $SERVER_IP"
        echo -e "   ${BLUE}Порт:${NC} 8388"
        echo -e "   ${BLUE}Метод:${NC} chacha20-ietf-poly1305"
        echo -e "   ${BLUE}Пароль:${NC} $PASSWORD"
        echo ""
        echo -e "${YELLOW}⚠️  Сохраните пароль!${NC}"
    fi
    
else
    echo -e "${RED}❌ Shadowsocks не запустился${NC}"
    echo ""
    echo -e "${YELLOW}Последние логи:${NC}"
    sudo journalctl -u shadowsocks-libev -n 30 --no-pager
    echo ""
    echo -e "${YELLOW}Проверка команды:${NC}"
    echo "  $SS_SERVER -c $CONFIG_PATH -t"
    echo ""
    echo -e "${YELLOW}Попробуйте запустить вручную:${NC}"
    echo "  sudo $SS_SERVER -c $CONFIG_PATH -u -v"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Готово! Shadowsocks работает.${NC}"

