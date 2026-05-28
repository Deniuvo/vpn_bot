#!/bin/bash
# Быстрая проверка работы Shadowsocks

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔍 Проверка Shadowsocks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Статус сервиса
echo -e "${YELLOW}[1/4] Статус сервиса:${NC}"
if sudo systemctl is-active --quiet shadowsocks-libev; then
    echo -e "${GREEN}✅ Сервис запущен${NC}"
    sudo systemctl status shadowsocks-libev --no-pager | head -n 3
else
    echo -e "${RED}❌ Сервис НЕ запущен${NC}"
fi
echo ""

# 2. Проверка порта
echo -e "${YELLOW}[2/4] Проверка порта 8388:${NC}"
PORT_CHECK=$(sudo netstat -tulnp 2>/dev/null | grep 8388 || sudo ss -tulnp 2>/dev/null | grep 8388)
if [ -n "$PORT_CHECK" ]; then
    echo -e "${GREEN}✅ Порт 8388 слушается:${NC}"
    echo "$PORT_CHECK" | head -n 2
else
    echo -e "${RED}❌ Порт 8388 НЕ слушается${NC}"
fi
echo ""

# 3. Проверка процесса
echo -e "${YELLOW}[3/4] Проверка процесса ss-server:${NC}"
PROCESS_CHECK=$(ps aux | grep "[s]s-server" | head -n 1)
if [ -n "$PROCESS_CHECK" ]; then
    echo -e "${GREEN}✅ Процесс запущен:${NC}"
    echo "$PROCESS_CHECK" | awk '{print "   PID:", $2, "| Команда:", substr($0, index($0,$11))}'
else
    echo -e "${RED}❌ Процесс НЕ найден${NC}"
fi
echo ""

# 4. Последние логи
echo -e "${YELLOW}[4/4] Последние логи (5 строк):${NC}"
RECENT_LOGS=$(sudo journalctl -u shadowsocks-libev -n 5 --no-pager 2>/dev/null | tail -n 5)
if [ -n "$RECENT_LOGS" ]; then
    echo "$RECENT_LOGS"
    
    # Проверка на ошибки
    if echo "$RECENT_LOGS" | grep -qi "error\|failed\|invalid"; then
        echo -e "${RED}⚠️  Обнаружены ошибки в логах${NC}"
    else
        echo -e "${GREEN}✅ Ошибок в логах нет${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Логи не найдены${NC}"
fi
echo ""

# Итоговая проверка
echo -e "${BLUE}========================================${NC}"
if sudo systemctl is-active --quiet shadowsocks-libev && [ -n "$PORT_CHECK" ]; then
    echo -e "${GREEN}✅ Shadowsocks РАБОТАЕТ!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Показываем параметры подключения
    if [ -f /etc/shadowsocks-libev/config.json ]; then
        PASSWORD=$(grep -o '"password": "[^"]*"' /etc/shadowsocks-libev/config.json | cut -d'"' -f4 2>/dev/null || echo "не найден")
        SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
        
        echo -e "${YELLOW}📋 Параметры подключения:${NC}"
        echo -e "   ${BLUE}Сервер:${NC} ${SERVER_IP}"
        echo -e "   ${BLUE}Порт:${NC} 8388"
        echo -e "   ${BLUE}Метод:${NC} chacha20-ietf-poly1305"
        echo -e "   ${BLUE}Пароль:${NC} ${PASSWORD}"
        echo ""
        echo -e "${GREEN}✅ Готово к использованию!${NC}"
        echo ""
        echo -e "${YELLOW}Следующий шаг:${NC} Обновить код бота для генерации конфигов с портом Shadowsocks (8388)"
    fi
else
    echo -e "${RED}❌ Shadowsocks НЕ РАБОТАЕТ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Попробуйте:${NC}"
    echo "   1. Перезапустить: sudo systemctl restart shadowsocks-libev"
    echo "   2. Проверить логи: sudo journalctl -u shadowsocks-libev -n 50"
    echo "   3. Запустить скрипт исправления: sudo bash fix_systemd_override.sh"
fi
echo ""

