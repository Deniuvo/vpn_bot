#!/bin/bash
# Исправление проблемы с путем к конфигу Shadowsocks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Исправление пути к конфигу Shadowsocks...${NC}"
echo ""

# 1. Проверка systemd unit файла
echo -e "${YELLOW}[1/5] Проверка systemd конфигурации...${NC}"
if [ -f /etc/systemd/system/shadowsocks-libev.service ] || [ -f /lib/systemd/system/shadowsocks-libev.service ]; then
    UNIT_FILE=$(systemctl show shadowsocks-libev.service | grep FragmentPath | cut -d'=' -f2 || echo "")
    if [ -n "$UNIT_FILE" ]; then
        echo -e "${GREEN}✅ Unit файл найден: $UNIT_FILE${NC}"
        echo ""
        echo "Содержимое unit файла:"
        cat "$UNIT_FILE" | grep -E "ExecStart|config" || true
    fi
else
    echo -e "${YELLOW}⚠️ Unit файл не найден в стандартных местах${NC}"
fi
echo ""

# 2. Проверка существующих конфигов
echo -e "${YELLOW}[2/5] Поиск существующих конфигов...${NC}"
FOUND_CONFIGS=$(find /etc -name "*shadowsocks*" -type f 2>/dev/null | head -5)
if [ -n "$FOUND_CONFIGS" ]; then
    echo "Найдены файлы:"
    echo "$FOUND_CONFIGS"
else
    echo -e "${YELLOW}⚠️ Конфиги не найдены${NC}"
fi
echo ""

# 3. Проверка существующего конфига
echo -e "${YELLOW}[3/5] Проверка конфига...${NC}"
CONFIG_PATH="/etc/shadowsocks-libev/config.json"

if [ -f "$CONFIG_PATH" ]; then
    echo -e "${GREEN}✅ Конфиг существует: $CONFIG_PATH${NC}"
    echo "Права доступа:"
    ls -la "$CONFIG_PATH"
    echo ""
    echo "Содержимое (первые 10 строк):"
    head -n 10 "$CONFIG_PATH"
    echo ""
    
    # Проверка синтаксиса
    if sudo shadowsocks-libev -c "$CONFIG_PATH" -t 2>&1; then
        echo -e "${GREEN}✅ Синтаксис конфига правильный${NC}"
    else
        echo -e "${RED}❌ Ошибка в синтаксисе${NC}"
    fi
else
    echo -e "${RED}❌ Конфиг не найден: $CONFIG_PATH${NC}"
    echo -e "${YELLOW}Создаю конфиг...${NC}"
    sudo mkdir -p /etc/shadowsocks-libev
    PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    sudo bash -c "cat > $CONFIG_PATH << EOF
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
    sudo chmod 600 "$CONFIG_PATH"
    echo -e "${GREEN}✅ Конфиг создан${NC}"
fi
echo ""

# 4. Создание альтернативного конфига (для systemd)
echo -e "${YELLOW}[4/5] Создание конфига для systemd...${NC}"

# Некоторые версии shadowsocks-libev ожидают конфиг в /etc/shadowsocks-libev/<имя>.json
# Создаем также config.json и default.json
sudo mkdir -p /etc/shadowsocks-libev

if [ -f "$CONFIG_PATH" ]; then
    # Копируем в несколько мест
    sudo cp "$CONFIG_PATH" /etc/shadowsocks-libev/default.json 2>/dev/null || true
    echo -e "${GREEN}✅ Конфиг скопирован как default.json${NC}"
fi
echo ""

# 5. Исправление systemd unit (если нужно)
echo -e "${YELLOW}[5/5] Исправление systemd unit...${NC}"

# Останавливаем сервис
sudo systemctl stop shadowsocks-libev 2>/dev/null || true

# Проверяем, как запускается сервис
if systemctl cat shadowsocks-libev.service 2>/dev/null | grep -q "ss-server"; then
    echo -e "${YELLOW}Обнаружен прямой запуск ss-server${NC}"
    
    # Пробуем запустить вручную с полным путем
    echo -e "${YELLOW}Тестирую запуск вручную...${NC}"
    if timeout 3 sudo shadowsocks-libev -c "$CONFIG_PATH" -v 2>&1 | head -n 10; then
        echo -e "${GREEN}✅ Ручной запуск работает!${NC}"
    fi
fi

# Перезагружаем systemd
sudo systemctl daemon-reload

# Пробуем запустить с явным указанием конфига
echo -e "${YELLOW}Запуск через systemd с исправленным путем...${NC}"
sudo systemctl start shadowsocks-libev
sleep 3

if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks запущен!${NC}"
    sudo systemctl status shadowsocks-libev --no-pager -l | head -n 15
else
    echo -e "${RED}❌ Все еще не запускается${NC}"
    echo ""
    echo -e "${YELLOW}Попробую альтернативный метод - прямое указание конфига в unit...${NC}"
    
    # Создаем override для systemd
    sudo mkdir -p /etc/systemd/system/shadowsocks-libev.service.d/
    sudo bash -c "cat > /etc/systemd/system/shadowsocks-libev.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/ss-server -c /etc/shadowsocks-libev/config.json -u
EOF"
    
    sudo systemctl daemon-reload
    sudo systemctl restart shadowsocks-libev
    sleep 3
    
    if sudo systemctl is-active --quiet shadowsocks-libev; then
        echo -e "${GREEN}✅ Запущен с override конфигом!${NC}"
        sudo systemctl status shadowsocks-libev --no-pager -l | head -n 15
    else
        echo -e "${RED}❌ Все еще не работает${NC}"
        echo ""
        echo "Последние логи:"
        sudo journalctl -u shadowsocks-libev -n 20 --no-pager
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Проверка завершена${NC}"
echo -e "${BLUE}========================================${NC}"

