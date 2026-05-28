#!/bin/bash
# Скрипт для автоматической установки и настройки WireGuard на сервере

set -e  # Остановка при ошибке

echo "🔐 Начинаю установку WireGuard..."

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите скрипт с правами root: sudo bash setup_wireguard.sh"
    exit 1
fi

# 1. Установка WireGuard
echo ""
echo "📦 Шаг 1: Установка WireGuard..."
apt update -qq
apt install -y wireguard wireguard-tools

# Проверка установки
if ! command -v wg &> /dev/null; then
    echo "❌ Ошибка установки WireGuard"
    exit 1
fi
echo "✅ WireGuard установлен"

# 2. Генерация ключей
echo ""
echo "🔑 Шаг 2: Генерация ключей сервера..."
cd /etc/wireguard

# Генерируем ключи, если их еще нет
if [ ! -f private.key ]; then
    wg genkey | tee private.key | wg pubkey > public.key
    chmod 600 private.key
    echo "✅ Ключи сгенерированы"
else
    echo "⚠️  Ключи уже существуют, пропускаю генерацию"
fi

PRIVATE_KEY=$(cat private.key)
PUBLIC_KEY=$(cat public.key)

echo "📋 Публичный ключ сервера: $PUBLIC_KEY"
echo "⚠️  Сохраните этот ключ - он понадобится для бота!"

# 3. Определение сетевого интерфейса
echo ""
echo "🌐 Шаг 3: Определение сетевого интерфейса..."
# Получаем основной интерфейс (не loopback, не wg0)
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)

if [ -z "$MAIN_INTERFACE" ]; then
    echo "⚠️  Не удалось определить интерфейс автоматически"
    echo "Пожалуйста, укажите имя вашего сетевого интерфейса:"
    read -p "Имя интерфейса (например, eth0, ens3): " MAIN_INTERFACE
else
    echo "✅ Найден основной интерфейс: $MAIN_INTERFACE"
fi

# 4. Получение публичного IP
echo ""
echo "📍 Шаг 4: Определение публичного IP..."
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)

if [ -z "$PUBLIC_IP" ]; then
    echo "⚠️  Не удалось определить публичный IP автоматически"
    read -p "Введите публичный IP сервера: " PUBLIC_IP
else
    echo "✅ Публичный IP: $PUBLIC_IP"
fi

# 5. Создание конфигурации
echo ""
echo "⚙️  Шаг 5: Создание конфигурации WireGuard..."
CONFIG_FILE="/etc/wireguard/wg0.conf"

# Определяем SSH порт (обычно 22, но может быть изменен)
SSH_PORT=$(grep -E "^Port|^#Port" /etc/ssh/sshd_config 2>/dev/null | grep -v "^#" | awk '{print $2}' | head -n1)
SSH_PORT=${SSH_PORT:-22}

if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  Конфигурация уже существует: $CONFIG_FILE"
    read -p "Перезаписать? (y/N): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Пропускаю создание конфигурации"
    else
        cat > "$CONFIG_FILE" <<EOF
[Interface]
PrivateKey = $PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
# Защита SSH: маршрутизация SSH трафика напрямую через основной интерфейс
# SSH трафик НЕ будет идти через WireGuard - это защитит доступ к серверу
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE; iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT; iptables -A OUTPUT -o $MAIN_INTERFACE -p tcp --sport $SSH_PORT -j ACCEPT; iptables -A OUTPUT -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE; iptables -t nat -D POSTROUTING -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT; iptables -D OUTPUT -o $MAIN_INTERFACE -p tcp --sport $SSH_PORT -j ACCEPT; iptables -D OUTPUT -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT
EOF
        chmod 600 "$CONFIG_FILE"
        echo "✅ Конфигурация создана с защитой SSH (порт $SSH_PORT)"
    fi
else
    cat > "$CONFIG_FILE" <<EOF
[Interface]
PrivateKey = $PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
# Защита SSH: маршрутизация SSH трафика напрямую через основной интерфейс
# SSH трафик НЕ будет идти через WireGuard - это защитит доступ к серверу
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE; iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT; iptables -A OUTPUT -o $MAIN_INTERFACE -p tcp --sport $SSH_PORT -j ACCEPT; iptables -A OUTPUT -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE; iptables -t nat -D POSTROUTING -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT; iptables -D OUTPUT -o $MAIN_INTERFACE -p tcp --sport $SSH_PORT -j ACCEPT; iptables -D OUTPUT -o $MAIN_INTERFACE -p tcp --dport $SSH_PORT -j ACCEPT
EOF
    chmod 600 "$CONFIG_FILE"
    echo "✅ Конфигурация создана с защитой SSH (порт $SSH_PORT)"
fi

# 6. Включение IP forwarding
echo ""
echo "🔄 Шаг 6: Включение IP forwarding..."
sysctl -w net.ipv4.ip_forward=1
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
fi
echo "✅ IP forwarding включен"

# 7. Настройка файрвола
echo ""
echo "🔥 Шаг 7: Настройка файрвола..."
if command -v ufw &> /dev/null; then
    ufw allow 51820/udp
    ufw allow 5000/tcp
    echo "✅ Порты открыты в UFW"
else
    iptables -A INPUT -p udp --dport 51820 -j ACCEPT 2>/dev/null || true
    iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true
    echo "✅ Правила iptables добавлены"
fi

# 8. Запуск WireGuard
echo ""
echo "🚀 Шаг 8: Запуск WireGuard..."
wg-quick down wg0 2>/dev/null || true
wg-quick up wg0
echo "✅ WireGuard запущен"

# 9. Автозапуск
echo ""
echo "🔄 Шаг 9: Настройка автозапуска..."
systemctl enable wg-quick@wg0
echo "✅ Автозапуск настроен"

# 10. Проверка
echo ""
echo "✅ Проверка статуса..."
wg show wg0

echo ""
echo "========================================="
echo "✅ WireGuard успешно установлен и настроен!"
echo "========================================="
echo ""
echo "📋 Важные данные для настройки бота:"
echo ""
echo "   Публичный IP сервера: $PUBLIC_IP"
echo "   Публичный ключ WireGuard: $PUBLIC_KEY"
echo ""
echo "🔧 Установите переменные окружения:"
echo ""
echo "   export SERVER_IP=\"$PUBLIC_IP\""
echo "   export SERVER_PUBLIC_KEY=\"$PUBLIC_KEY\""
echo ""
echo "📝 Или добавьте в ~/.bashrc для постоянного сохранения:"
echo ""
echo "   echo 'export SERVER_IP=\"$PUBLIC_IP\"' >> ~/.bashrc"
echo "   echo 'export SERVER_PUBLIC_KEY=\"$PUBLIC_KEY\"' >> ~/.bashrc"
echo ""
echo "🚀 Теперь можно запускать бота!"
echo ""

