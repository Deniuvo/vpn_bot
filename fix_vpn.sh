#!/bin/bash
# Комплексный скрипт диагностики и исправления VPN

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 Диагностика VPN..."
echo "=================================="
echo ""

# 1. Проверка WireGuard
echo "1️⃣ Проверка WireGuard..."

if ! command -v wg &> /dev/null; then
    echo -e "${RED}❌ WireGuard не установлен!${NC}"
    echo "   Установите: apt install wireguard wireguard-tools"
    exit 1
fi

if ! ip link show wg0 &> /dev/null; then
    echo -e "${RED}❌ Интерфейс wg0 не существует!${NC}"
    echo "   Запустите: wg-quick up wg0"
    exit 1
fi

if ip link show wg0 | grep -q "UP"; then
    echo -e "${GREEN}✅ WireGuard запущен${NC}"
else
    echo -e "${RED}❌ WireGuard не запущен!${NC}"
    echo "   Запускаю WireGuard..."
    wg-quick up wg0
    sleep 2
fi

# Проверка peers
peer_count=$(wg show wg0 peers 2>/dev/null | wc -l)
echo "   Количество peers: $peer_count"

if [ "$peer_count" -eq 0 ]; then
    echo -e "${YELLOW}⚠️ На сервере нет peers!${NC}"
    echo "   Это основная причина, почему VPN не работает!"
    echo ""
    echo "🔧 Решение:"
    echo "   Запустите: python3 find_and_add_peer.py"
    echo "   Или добавьте peer вручную через скрипт fix_peer_manual.sh"
fi

echo ""

# 2. Проверка IP forwarding
echo "2️⃣ Проверка IP forwarding..."
ip_forward=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo "0")
if [ "$ip_forward" = "1" ]; then
    echo -e "${GREEN}✅ IP forwarding включен${NC}"
else
    echo -e "${RED}❌ IP forwarding ОТКЛЮЧЕН!${NC}"
    echo "   Включаю IP forwarding..."
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    sysctl -p
    echo -e "${GREEN}✅ IP forwarding включен${NC}"
fi

echo ""

# 3. Проверка iptables правил
echo "3️⃣ Проверка iptables правил..."

if command -v iptables &> /dev/null; then
    # Проверка FORWARD
    if iptables -L FORWARD -n -v 2>/dev/null | grep -q "wg0"; then
        echo -e "${GREEN}✅ FORWARD правило для wg0 существует${NC}"
    else
        echo -e "${RED}❌ FORWARD правило отсутствует!${NC}"
        echo "   Добавляю правило..."
        iptables -A FORWARD -i wg0 -j ACCEPT
        echo -e "${GREEN}✅ FORWARD правило добавлено${NC}"
    fi
    
    # Проверка MASQUERADE
    if iptables -t nat -L POSTROUTING -n -v 2>/dev/null | grep -q "MASQUERADE"; then
        echo -e "${GREEN}✅ NAT MASQUERADE правило существует${NC}"
    else
        echo -e "${RED}❌ NAT MASQUERADE правило отсутствует!${NC}"
        echo "   Добавляю правило..."
        MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)
        iptables -t nat -A POSTROUTING -o "$MAIN_INTERFACE" -j MASQUERADE
        echo -e "${GREEN}✅ MASQUERADE правило добавлено для $MAIN_INTERFACE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ iptables не найден${NC}"
fi

echo ""

# 4. Проверка файрвола
echo "4️⃣ Проверка файрвола..."
if command -v ufw &> /dev/null; then
    ufw_status=$(ufw status 2>/dev/null | head -n 1 || echo "inactive")
    if echo "$ufw_status" | grep -q "inactive"; then
        echo -e "${YELLOW}⚠️ UFW неактивен${NC}"
    else
        if ufw status | grep -q "51820/udp"; then
            echo -e "${GREEN}✅ Порт 51820 открыт в UFW${NC}"
        else
            echo -e "${YELLOW}⚠️ Порт 51820 может быть закрыт${NC}"
            echo "   Открываю порт..."
            ufw allow 51820/udp
        fi
    fi
fi

echo ""

# 5. Проверка конфигурации
echo "5️⃣ Проверка конфигурации..."
if [ -f "/etc/wireguard/wg0.conf" ]; then
    if grep -q "MASQUERADE" /etc/wireguard/wg0.conf; then
        echo -e "${GREEN}✅ Конфигурация содержит MASQUERADE${NC}"
    else
        echo -e "${RED}❌ Конфигурация не содержит MASQUERADE!${NC}"
        echo "   Нужно обновить /etc/wireguard/wg0.conf"
    fi
else
    echo -e "${RED}❌ Конфигурационный файл не найден!${NC}"
fi

echo ""
echo "=================================="
echo ""

# Итоговая проверка peers
if [ "$peer_count" -eq 0 ]; then
    echo -e "${RED}❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет peers на сервере!${NC}"
    echo ""
    echo "🔧 СРОЧНОЕ РЕШЕНИЕ:"
    echo ""
    echo "1. Добавьте peers автоматически:"
    echo "   cd /root/vpn_bot"
    echo "   source vpn_env/bin/activate"
    echo "   python3 find_and_add_peer.py"
    echo ""
    echo "2. Или добавьте вручную:"
    echo "   wg set wg0 peer <PUBLIC_KEY> allowed-ips <IP>/32"
    echo ""
    echo "3. После добавления проверьте:"
    echo "   wg show wg0"
    echo ""
else
    echo -e "${GREEN}✅ Основные проверки пройдены!${NC}"
    echo ""
    echo "💡 Если VPN все еще не работает:"
    echo "   1. Проверьте подключение на клиенте"
    echo "   2. Проверьте IP адрес: https://ifconfig.me"
    echo "   3. Проверьте логи: journalctl -u wg-quick@wg0 -n 50"
fi

echo ""
echo "📊 Текущий статус WireGuard:"
wg show wg0 2>/dev/null || echo "⚠️ Не удалось получить статус"

