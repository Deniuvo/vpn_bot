#!/bin/bash
# Исправление systemd override с правильными параметрами

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Исправление systemd override для Shadowsocks${NC}"
echo ""

CONFIG_PATH="/etc/shadowsocks-libev/config.json"

# 1. Проверка конфига
echo -e "${YELLOW}[1/4] Проверка конфига...${NC}"
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}❌ Конфиг не найден!${NC}"
    exit 1
fi

# Проверка синтаксиса
if /usr/bin/ss-server -c "$CONFIG_PATH" -t 2>&1 | grep -q -i "error"; then
    echo -e "${RED}❌ Ошибка в конфиге!${NC}"
    /usr/bin/ss-server -c "$CONFIG_PATH" -t
    exit 1
fi
echo -e "${GREEN}✅ Конфиг правильный${NC}"
echo ""

# 2. Остановка старого сервиса
echo -e "${YELLOW}[2/4] Остановка сервиса...${NC}"
sudo systemctl stop shadowsocks-libev 2>/dev/null || true
sleep 1
echo -e "${GREEN}✅ Сервис остановлен${NC}"
echo ""

# 3. Создание правильного override
echo -e "${YELLOW}[3/4] Создание systemd override...${NC}"
sudo mkdir -p /etc/systemd/system/shadowsocks-libev.service.d/

# Создаем override с ПРАВИЛЬНЫМ форматом
sudo bash -c "cat > /etc/systemd/system/shadowsocks-libev.service.d/override.conf << 'OVERRIDE_EOF'
[Service]
# Очищаем старую команду
ExecStart=
# Новая команда с полным путем к конфигу в кавычках
ExecStart=/usr/bin/ss-server -c \"$CONFIG_PATH\" -u
# Включаем логирование
StandardOutput=journal
StandardError=journal
# Автоперезапуск при ошибке
Restart=always
RestartSec=5
OVERRIDE_EOF"

echo -e "${GREEN}✅ Override создан${NC}"
echo ""
echo "Содержимое override:"
cat /etc/systemd/system/shadowsocks-libev.service.d/override.conf
echo ""

# 4. Перезапуск
echo -e "${YELLOW}[4/4] Перезапуск сервиса...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart shadowsocks-libev
sleep 4

# Проверка
if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks запущен!${NC}"
    echo ""
    sudo systemctl status shadowsocks-libev --no-pager -l | head -n 20
    
    # Показываем пароль из конфига
    if [ -f "$CONFIG_PATH" ]; then
        PASSWORD=$(grep -o '"password": "[^"]*"' "$CONFIG_PATH" | cut -d'"' -f4)
        SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
        
        echo ""
        echo -e "${BLUE}========================================${NC}"
        echo -e "${GREEN}🎉 Успешно запущен!${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        echo -e "${YELLOW}📋 Параметры подключения:${NC}"
        echo -e "   Сервер: ${SERVER_IP}"
        echo -e "   Порт: 8388"
        echo -e "   Пароль: ${PASSWORD}"
        echo ""
    fi
else
    echo -e "${RED}❌ Все еще не запускается${NC}"
    echo ""
    echo -e "${YELLOW}Логи:${NC}"
    sudo journalctl -u shadowsocks-libev -n 20 --no-pager
    
    echo ""
    echo -e "${YELLOW}Проверка команды:${NC}"
    echo "sudo /usr/bin/ss-server -c \"$CONFIG_PATH\" -u -v"
    
    echo ""
    echo -e "${YELLOW}Попробуйте запустить вручную:${NC}"
    echo "sudo nohup /usr/bin/ss-server -c \"$CONFIG_PATH\" -u > /var/log/shadowsocks.log 2>&1 &"
fi

