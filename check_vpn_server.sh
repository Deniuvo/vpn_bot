#!/bin/bash
# Скрипт диагностики VPN сервера WireGuard

echo "🔍 Диагностика VPN сервера WireGuard"
echo "===================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# 1. Проверка WireGuard
echo "1️⃣ Проверка WireGuard..."
if command -v wg &> /dev/null; then
    echo -e "${GREEN}✅ WireGuard установлен${NC}"
    wg_version=$(wg --version 2>&1 | head -n 1)
    echo "   Версия: $wg_version"
else
    echo -e "${RED}❌ WireGuard НЕ установлен!${NC}"
    errors=$((errors + 1))
fi
echo ""

# 2. Проверка интерфейса wg0
echo "2️⃣ Проверка интерфейса wg0..."
if ip link show wg0 &> /dev/null; then
    echo -e "${GREEN}✅ Интерфейс wg0 существует${NC}"
    
    # Проверяем, запущен ли
    if ip link show wg0 | grep -q "UP"; then
        echo -e "${GREEN}✅ Интерфейс wg0 запущен${NC}"
        
        # Показываем IP адрес
        wg0_ip=$(ip addr show wg0 | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        echo "   IP адрес: $wg0_ip"
        
        # Показываем количество peers
        peer_count=$(wg show wg0 peers | wc -l)
        echo "   Количество peers: $peer_count"
    else
        echo -e "${RED}❌ Интерфейс wg0 НЕ запущен!${NC}"
        errors=$((errors + 1))
        echo "   Запустите: wg-quick up wg0"
    fi
else
    echo -e "${RED}❌ Интерфейс wg0 НЕ существует!${NC}"
    errors=$((errors + 1))
    echo "   Проверьте конфигурацию в /etc/wireguard/wg0.conf"
fi
echo ""

# 3. Проверка IP forwarding
echo "3️⃣ Проверка IP forwarding..."
ip_forward=$(cat /proc/sys/net/ipv4/ip_forward)
if [ "$ip_forward" = "1" ]; then
    echo -e "${GREEN}✅ IP forwarding включен${NC}"
else
    echo -e "${RED}❌ IP forwarding ОТКЛЮЧЕН!${NC}"
    errors=$((errors + 1))
    echo "   Включите: echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf && sysctl -p"
fi
echo ""

# 4. Проверка iptables правил
echo "4️⃣ Проверка iptables правил..."
if command -v iptables &> /dev/null; then
    # Проверка FORWARD правила
    if iptables -L FORWARD -n -v | grep -q "wg0"; then
        echo -e "${GREEN}✅ FORWARD правило для wg0 существует${NC}"
    else
        echo -e "${RED}❌ FORWARD правило для wg0 НЕ найдено!${NC}"
        errors=$((errors + 1))
        echo "   Добавьте: iptables -A FORWARD -i wg0 -j ACCEPT"
    fi
    
    # Проверка NAT MASQUERADE
    if iptables -t nat -L POSTROUTING -n -v | grep -q "MASQUERADE"; then
        echo -e "${GREEN}✅ NAT MASQUERADE правило существует${NC}"
        
        # Находим основной интерфейс
        main_interface=$(ip route | grep default | awk '{print $5}' | head -n 1)
        echo "   Основной интерфейс: $main_interface"
    else
        echo -e "${RED}❌ NAT MASQUERADE правило НЕ найдено!${NC}"
        errors=$((errors + 1))
        echo "   Добавьте: iptables -t nat -A POSTROUTING -o <интерфейс> -j MASQUERADE"
    fi
else
    echo -e "${YELLOW}⚠️ iptables не установлен или не используется${NC}"
    warnings=$((warnings + 1))
fi
echo ""

# 5. Проверка файрвола
echo "5️⃣ Проверка файрвола..."
if command -v ufw &> /dev/null; then
    ufw_status=$(ufw status | head -n 1)
    echo "   UFW статус: $ufw_status"
    
    if ufw status | grep -q "51820/udp"; then
        echo -e "${GREEN}✅ Порт 51820 (WireGuard) открыт в UFW${NC}"
    else
        echo -e "${YELLOW}⚠️ Порт 51820 может быть закрыт в UFW${NC}"
        warnings=$((warnings + 1))
        echo "   Откройте: ufw allow 51820/udp"
    fi
else
    echo -e "${YELLOW}⚠️ UFW не используется${NC}"
fi
echo ""

# 6. Проверка статуса WireGuard сервиса
echo "6️⃣ Проверка сервиса WireGuard..."
if systemctl is-active --quiet wg-quick@wg0; then
    echo -e "${GREEN}✅ Сервис wg-quick@wg0 активен${NC}"
else
    echo -e "${RED}❌ Сервис wg-quick@wg0 НЕ активен!${NC}"
    errors=$((errors + 1))
    echo "   Запустите: systemctl start wg-quick@wg0"
    echo "   Включите автозапуск: systemctl enable wg-quick@wg0"
fi
echo ""

# 7. Проверка конфигурации сервера
echo "7️⃣ Проверка конфигурации..."
if [ -f "/etc/wireguard/wg0.conf" ]; then
    echo -e "${GREEN}✅ Конфигурационный файл существует${NC}"
    
    # Проверяем наличие PostUp с MASQUERADE
    if grep -q "MASQUERADE" /etc/wireguard/wg0.conf; then
        echo -e "${GREEN}✅ PostUp содержит MASQUERADE${NC}"
    else
        echo -e "${RED}❌ PostUp НЕ содержит MASQUERADE!${NC}"
        errors=$((errors + 1))
    fi
    
    # Проверяем основной интерфейс в конфиге
    main_if=$(grep -i "PostUp" /etc/wireguard/wg0.conf | grep -oE "eth[0-9]|ens[0-9]" | head -n 1)
    if [ -n "$main_if" ]; then
        echo "   Основной интерфейс в конфиге: $main_if"
        
        # Проверяем, существует ли этот интерфейс
        if ip link show "$main_if" &> /dev/null; then
            echo -e "${GREEN}✅ Интерфейс $main_if существует${NC}"
        else
            echo -e "${RED}❌ Интерфейс $main_if НЕ существует!${NC}"
            errors=$((errors + 1))
            echo "   Проверьте конфигурацию и замените на правильный интерфейс"
        fi
    else
        echo -e "${YELLOW}⚠️ Не удалось определить основной интерфейс из конфига${NC}"
        warnings=$((warnings + 1))
    fi
else
    echo -e "${RED}❌ Конфигурационный файл НЕ найден!${NC}"
    errors=$((errors + 1))
fi
echo ""

# Итоги
echo "===================================="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ Все критические проверки пройдены!${NC}"
    if [ $warnings -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Обнаружено $warnings предупреждений${NC}"
    fi
    echo ""
    echo "💡 Если VPN все еще не работает:"
    echo "   1. Проверьте, что клиент правильно подключен"
    echo "   2. Проверьте логи WireGuard: journalctl -u wg-quick@wg0 -n 50"
    echo "   3. Проверьте подключение на клиенте: wg show"
else
    echo -e "${RED}❌ Обнаружено $errors критических ошибок!${NC}"
    if [ $warnings -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Обнаружено $warnings предупреждений${NC}"
    fi
    echo ""
    echo "🔧 Исправьте ошибки выше и запустите скрипт снова"
fi

