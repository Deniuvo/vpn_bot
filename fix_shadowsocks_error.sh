#!/bin/bash
# Диагностика и исправление ошибок запуска Shadowsocks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Диагностика проблемы Shadowsocks...${NC}"
echo ""

# 1. Проверка логов
echo -e "${YELLOW}1. Проверка логов сервиса...${NC}"
echo ""
sudo journalctl -u shadowsocks-libev -n 30 --no-pager
echo ""

# 2. Проверка синтаксиса конфига
echo -e "${YELLOW}2. Проверка синтаксиса конфига...${NC}"
if sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -t 2>&1; then
    echo -e "${GREEN}✅ Синтаксис конфига правильный${NC}"
else
    echo -e "${RED}❌ Ошибка в синтаксисе конфига${NC}"
fi
echo ""

# 3. Проверка наличия плагина obfs-server
echo -e "${YELLOW}3. Проверка плагина obfs-server...${NC}"
if command -v obfs-server &> /dev/null; then
    echo -e "${GREEN}✅ Плагин obfs-server установлен${NC}"
    obfs-server --version 2>/dev/null || echo "Проверка версии..."
else
    echo -e "${RED}❌ Плагин obfs-server НЕ найден!${NC}"
    echo -e "${YELLOW}Устанавливаю simple-obfs...${NC}"
    sudo apt install -y simple-obfs
fi
echo ""

# 4. Проверка прав доступа к конфигу
echo -e "${YELLOW}4. Проверка прав доступа...${NC}"
if [ -f /etc/shadowsocks-libev/config.json ]; then
    ls -la /etc/shadowsocks-libev/config.json
    echo -e "${GREEN}✅ Файл конфига существует${NC}"
else
    echo -e "${RED}❌ Файл конфига не найден!${NC}"
    exit 1
fi
echo ""

# 5. Попытка запуска в тестовом режиме
echo -e "${YELLOW}5. Тестовый запуск Shadowsocks...${NC}"
sudo systemctl stop shadowsocks-libev 2>/dev/null || true

# Запуск в foreground для проверки ошибок
echo -e "${YELLOW}Запускаю в тестовом режиме (5 секунд)...${NC}"
timeout 5 sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -v 2>&1 || true
echo ""

# 6. Решение проблемы с плагином (если нужно)
echo -e "${YELLOW}6. Проверка конфигурации плагина...${NC}"
if grep -q "plugin" /etc/shadowsocks-libev/config.json; then
    echo "Конфиг содержит плагин, проверяю..."
    
    # Если плагин не работает, пробуем без него
    echo -e "${YELLOW}Создаю резервный конфиг без плагина для теста...${NC}"
    sudo cp /etc/shadowsocks-libev/config.json /etc/shadowsocks-libev/config.json.backup
    
    # Создаем тестовый конфиг без плагина
    PASSWORD=$(grep -o '"password": "[^"]*"' /etc/shadowsocks-libev/config.json | cut -d'"' -f4)
    sudo bash -c "cat > /etc/shadowsocks-libev/config_no_plugin.json << EOF
{
    \"server\": \"0.0.0.0\",
    \"server_port\": 8388,
    \"local_address\": \"127.0.0.1\",
    \"local_port\": 51820,
    \"password\": \"$PASSWORD\",
    \"timeout\": 300,
    \"method\": \"chacha20-ietf-poly1305\",
    \"fast_open\": true,
    \"mode\": \"tcp_and_udp\"
}
EOF"
    
    echo -e "${YELLOW}Тестирую конфиг без плагина...${NC}"
    if sudo shadowsocks-libev -c /etc/shadowsocks-libev/config_no_plugin.json -t 2>&1; then
        echo -e "${GREEN}✅ Конфиг без плагина работает!${NC}"
        echo -e "${YELLOW}Проблема в плагине obfs-server${NC}"
        echo ""
        echo "Выберите вариант:"
        echo "1. Использовать конфиг без плагина (работает, но без обфускации)"
        echo "2. Исправить конфиг с плагином"
        echo ""
        read -p "Ваш выбор (1/2): " choice
        
        if [ "$choice" == "1" ]; then
            sudo cp /etc/shadowsocks-libev/config_no_plugin.json /etc/shadowsocks-libev/config.json
            echo -e "${GREEN}✅ Использован конфиг без плагина${NC}"
        fi
    fi
fi
echo ""

# 7. Финальная проверка
echo -e "${YELLOW}7. Запуск сервиса...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart shadowsocks-libev
sleep 2

if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks успешно запущен!${NC}"
    sudo systemctl status shadowsocks-libev --no-pager -l
else
    echo -e "${RED}❌ Shadowsocks все еще не запускается${NC}"
    echo ""
    echo "Последние логи ошибок:"
    sudo journalctl -u shadowsocks-libev -n 20 --no-pager
fi

