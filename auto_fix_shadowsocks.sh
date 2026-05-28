#!/bin/bash
# Автоматическая настройка и исправление Shadowsocks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔧 Автоматическая настройка Shadowsocks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Проверка установки Shadowsocks
echo -e "${YELLOW}[1/8] Проверка установки Shadowsocks...${NC}"
if ! command -v shadowsocks-libev &> /dev/null; then
    echo -e "${RED}❌ Shadowsocks не установлен!${NC}"
    echo -e "${YELLOW}Устанавливаю Shadowsocks...${NC}"
    sudo apt update
    sudo apt install -y shadowsocks-libev simple-obfs
fi
echo -e "${GREEN}✅ Shadowsocks установлен${NC}"
echo ""

# 2. Проверка директории
echo -e "${YELLOW}[2/8] Проверка директории...${NC}"
if [ ! -d /etc/shadowsocks-libev ]; then
    sudo mkdir -p /etc/shadowsocks-libev
    sudo chmod 755 /etc/shadowsocks-libev
    echo -e "${GREEN}✅ Директория создана${NC}"
else
    echo -e "${GREEN}✅ Директория существует${NC}"
fi
echo ""

# 3. Получение пароля из существующего конфига или генерация нового
echo -e "${YELLOW}[3/8] Настройка пароля...${NC}"
if [ -f /etc/shadowsocks-libev/config.json ]; then
    EXISTING_PASSWORD=$(grep -o '"password": "[^"]*"' /etc/shadowsocks-libev/config.json | cut -d'"' -f4 || echo "")
    if [ -n "$EXISTING_PASSWORD" ]; then
        PASSWORD="$EXISTING_PASSWORD"
        echo -e "${GREEN}✅ Используется существующий пароль${NC}"
    else
        PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        echo -e "${YELLOW}⚠️ Новый пароль сгенерирован${NC}"
    fi
else
    PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    echo -e "${YELLOW}⚠️ Новый пароль сгенерирован${NC}"
fi
echo -e "${BLUE}📝 Пароль: ${PASSWORD}${NC}"
echo ""

# 4. Создание резервной копии существующего конфига
if [ -f /etc/shadowsocks-libev/config.json ]; then
    echo -e "${YELLOW}[4/8] Создание резервной копии...${NC}"
    sudo cp /etc/shadowsocks-libev/config.json /etc/shadowsocks-libev/config.json.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Резервная копия создана${NC}"
    echo ""
fi

# 5. Создание конфига БЕЗ плагина (работает надежнее)
echo -e "${YELLOW}[5/8] Создание конфигурации без плагина...${NC}"
sudo bash -c "cat > /etc/shadowsocks-libev/config.json << 'CONFIG_EOF'
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
CONFIG_EOF"

# Установка прав
sudo chmod 600 /etc/shadowsocks-libev/config.json
sudo chown root:root /etc/shadowsocks-libev/config.json

echo -e "${GREEN}✅ Конфиг создан${NC}"
echo ""

# 6. Проверка синтаксиса конфига
echo -e "${YELLOW}[6/8] Проверка синтаксиса конфига...${NC}"
if sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -t 2>&1 | grep -q "error"; then
    echo -e "${RED}❌ Ошибка в синтаксисе конфига!${NC}"
    sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -t
    exit 1
else
    echo -e "${GREEN}✅ Синтаксис конфига правильный${NC}"
fi
echo ""

# 7. Настройка файрвола
echo -e "${YELLOW}[7/8] Настройка файрвола...${NC}"

# UFW
if command -v ufw &> /dev/null; then
    sudo ufw allow 8388/tcp 2>/dev/null || true
    sudo ufw allow 8388/udp 2>/dev/null || true
    echo -e "${GREEN}✅ Порты открыты в UFW${NC}"
fi

# iptables
if command -v iptables &> /dev/null; then
    sudo iptables -A INPUT -p tcp --dport 8388 -j ACCEPT 2>/dev/null || true
    sudo iptables -A INPUT -p udp --dport 8388 -j ACCEPT 2>/dev/null || true
    echo -e "${GREEN}✅ Порты открыты в iptables${NC}"
fi
echo ""

# 8. Запуск Shadowsocks
echo -e "${YELLOW}[8/8] Запуск Shadowsocks...${NC}"

# Остановка старого процесса
sudo systemctl stop shadowsocks-libev 2>/dev/null || true
sleep 1

# Создание конфига также как default.json (для совместимости)
sudo cp /etc/shadowsocks-libev/config.json /etc/shadowsocks-libev/default.json 2>/dev/null || true

# Проверка, какой способ запуска использует systemd
if systemctl cat shadowsocks-libev.service 2>/dev/null | grep -q "/usr/bin/ss-server"; then
    echo -e "${YELLOW}Обнаружен прямой запуск ss-server, создаю override...${NC}"
    sudo mkdir -p /etc/systemd/system/shadowsocks-libev.service.d/
    sudo bash -c 'cat > /etc/systemd/system/shadowsocks-libev.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=/usr/bin/ss-server -c /etc/shadowsocks-libev/config.json -u
EOF'
fi

# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск сервиса
sudo systemctl enable shadowsocks-libev
sudo systemctl restart shadowsocks-libev

# Ожидание запуска
sleep 3

# Проверка статуса
if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Shadowsocks успешно запущен!${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 Настройка завершена успешно!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}📋 Информация о подключении:${NC}"
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    echo -e "   ${BLUE}Сервер:${NC} ${SERVER_IP}"
    echo -e "   ${BLUE}Порт:${NC} 8388"
    echo -e "   ${BLUE}Метод:${NC} chacha20-ietf-poly1305"
    echo -e "   ${BLUE}Пароль:${NC} ${PASSWORD}"
    echo -e "   ${BLUE}Режим:${NC} TCP и UDP"
    echo ""
    echo -e "${YELLOW}⚠️  ВАЖНО: Сохраните пароль!${NC}"
    echo ""
    echo -e "${YELLOW}📝 Полезные команды:${NC}"
    echo -e "   ${BLUE}Статус:${NC} sudo systemctl status shadowsocks-libev"
    echo -e "   ${BLUE}Логи:${NC} sudo journalctl -u shadowsocks-libev -f"
    echo -e "   ${BLUE}Перезапуск:${NC} sudo systemctl restart shadowsocks-libev"
    echo -e "   ${BLUE}Проверка порта:${NC} sudo netstat -tulnp | grep 8388"
    echo ""
    
    # Показываем статус
    sudo systemctl status shadowsocks-libev --no-pager -l | head -n 10
    
else
    echo -e "${RED}❌ Shadowsocks не запустился${NC}"
    echo ""
    echo -e "${YELLOW}Последние логи ошибок:${NC}"
    sudo journalctl -u shadowsocks-libev -n 30 --no-pager
    echo ""
    echo -e "${YELLOW}Попробуйте:${NC}"
    echo "   1. Проверить логи: sudo journalctl -u shadowsocks-libev -n 50"
    echo "   2. Проверить синтаксис: sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -t"
    echo "   3. Запустить вручную: sudo shadowsocks-libev -c /etc/shadowsocks-libev/config.json -v"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Готово! Shadowsocks работает и готов к использованию.${NC}"

