#!/bin/bash
# Проверка и исправление проблемы "Invalid config path"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Проверка проблемы "Invalid config path"...${NC}"
echo ""

# 1. Проверка существования конфига
CONFIG_PATH="/etc/shadowsocks-libev/config.json"
echo -e "${YELLOW}[1/6] Проверка конфига...${NC}"

if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}❌ Конфиг НЕ существует! Создаю...${NC}"
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
echo ""

# 2. Проверка прав доступа
echo -e "${YELLOW}[2/6] Проверка прав доступа...${NC}"
ls -la "$CONFIG_PATH"

# Устанавливаем правильные права
sudo chmod 644 "$CONFIG_PATH"
sudo chown root:root "$CONFIG_PATH" 2>/dev/null || true
echo -e "${GREEN}✅ Права установлены${NC}"
echo ""

# 3. Проверка синтаксиса JSON
echo -e "${YELLOW}[3/6] Проверка синтаксиса JSON...${NC}"
if python3 -m json.tool "$CONFIG_PATH" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ JSON синтаксис правильный${NC}"
else
    echo -e "${RED}❌ Ошибка в JSON!${NC}"
    python3 -m json.tool "$CONFIG_PATH" 2>&1 | head -n 10
    exit 1
fi
echo ""

# 4. Проверка ss-server может ли прочитать конфиг
echo -e "${YELLOW}[4/6] Проверка чтения конфига ss-server...${NC}"
if /usr/bin/ss-server -c "$CONFIG_PATH" -t 2>&1 | grep -q "error\|Error\|ERROR"; then
    ERROR_OUTPUT=$(/usr/bin/ss-server -c "$CONFIG_PATH" -t 2>&1)
    echo -e "${RED}❌ ss-server не может прочитать конфиг:${NC}"
    echo "$ERROR_OUTPUT"
    exit 1
else
    echo -e "${GREEN}✅ ss-server может прочитать конфиг${NC}"
    /usr/bin/ss-server -c "$CONFIG_PATH" -t 2>&1 | head -n 5
fi
echo ""

# 5. Проверка пути в systemd override
echo -e "${YELLOW}[5/6] Проверка systemd override...${NC}"
OVERRIDE_DIR="/etc/systemd/system/shadowsocks-libev.service.d/"
OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"

if [ -f "$OVERRIDE_FILE" ]; then
    echo "Содержимое override:"
    cat "$OVERRIDE_FILE"
    echo ""
    
    # Проверяем, правильно ли указан путь
    if ! grep -q "$CONFIG_PATH" "$OVERRIDE_FILE"; then
        echo -e "${RED}❌ Путь к конфигу в override НЕПРАВИЛЬНЫЙ!${NC}"
        echo -e "${YELLOW}Исправляю...${NC}"
        
        sudo bash -c "cat > $OVERRIDE_FILE << 'OVERRIDE_EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/ss-server -c $CONFIG_PATH -u
OVERRIDE_EOF"
        
        echo -e "${GREEN}✅ Override исправлен${NC}"
    else
        echo -e "${GREEN}✅ Путь в override правильный${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Override не существует, создаю...${NC}"
    sudo mkdir -p "$OVERRIDE_DIR"
    sudo bash -c "cat > $OVERRIDE_FILE << 'OVERRIDE_EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/ss-server -c $CONFIG_PATH -u
OVERRIDE_EOF"
    echo -e "${GREEN}✅ Override создан${NC}"
fi
echo ""

# 6. Тест ручного запуска
echo -e "${YELLOW}[6/6] Тест ручного запуска...${NC}"
sudo systemctl stop shadowsocks-libev 2>/dev/null || true
sleep 1

echo -e "${YELLOW}Запускаю в тестовом режиме (3 секунды)...${NC}"
timeout 3 sudo /usr/bin/ss-server -c "$CONFIG_PATH" -u -v 2>&1 | head -n 10 || echo "Процесс завершен (это нормально для теста)"

if [ ${PIPESTATUS[0]} -eq 124 ] || [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✅ Ручной запуск работает!${NC}"
else
    echo -e "${RED}❌ Ошибка при ручном запуске${NC}"
    exit 1
fi
echo ""

# 7. Перезапуск через systemd
echo -e "${YELLOW}Перезапуск через systemd...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart shadowsocks-libev
sleep 3

if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks запущен через systemd!${NC}"
    echo ""
    sudo systemctl status shadowsocks-libev --no-pager -l | head -n 15
    echo ""
    
    # Показываем пароль
    PASSWORD=$(grep -o '"password": "[^"]*"' "$CONFIG_PATH" | cut -d'"' -f4)
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 Shadowsocks работает!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}📋 Параметры подключения:${NC}"
    echo -e "   Сервер: ${SERVER_IP}"
    echo -e "   Порт: 8388"
    echo -e "   Метод: chacha20-ietf-poly1305"
    echo -e "   Пароль: ${PASSWORD}"
    echo ""
    echo -e "${YELLOW}⚠️  Сохраните пароль!${NC}"
    
else
    echo -e "${RED}❌ Все еще не запускается через systemd${NC}"
    echo ""
    echo -e "${YELLOW}Последние логи:${NC}"
    sudo journalctl -u shadowsocks-libev -n 20 --no-pager
    
    echo ""
    echo -e "${YELLOW}Попробуйте запустить вручную:${NC}"
    echo "sudo nohup /usr/bin/ss-server -c $CONFIG_PATH -u > /var/log/shadowsocks.log 2>&1 &"
    echo ""
    echo "Проверка:"
    echo "ps aux | grep ss-server"
    echo "sudo netstat -tulnp | grep 8388"
fi

