#!/bin/bash
# Скрипт для ручного добавления peer на WireGuard сервер
# Используйте, если бот не смог добавить peer автоматически

if [ "$#" -ne 2 ]; then
    echo "Использование: $0 <PUBLIC_KEY> <IP_ADDRESS>"
    echo "Пример: $0 AbCdEfGhIjKlMnOpQrStUvWxYz1234567890 10.0.0.5"
    exit 1
fi

PUBLIC_KEY="$1"
IP_ADDRESS="$2"

echo "🔧 Добавляю peer на WireGuard сервер..."
echo "   Public Key: ${PUBLIC_KEY:0:20}..."
echo "   IP Address: $IP_ADDRESS"

# Добавляем peer
wg set wg0 peer "$PUBLIC_KEY" allowed-ips "${IP_ADDRESS}/32"

if [ $? -eq 0 ]; then
    echo "✅ Peer успешно добавлен!"
    
    # Проверяем
    echo ""
    echo "📋 Текущие peers на сервере:"
    wg show wg0 peers
    
    echo ""
    echo "📊 Полная информация:"
    wg show wg0
else
    echo "❌ Ошибка при добавлении peer!"
    echo "Проверьте:"
    echo "  1. WireGuard запущен: wg-quick up wg0"
    echo "  2. У вас есть права root: sudo $0 ..."
    echo "  3. Public Key корректен"
    exit 1
fi

# Сохраняем в конфиг для постоянства после перезапуска
echo ""
read -p "Сохранить peer в /etc/wireguard/wg0.conf для постоянства? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "/etc/wireguard/wg0.conf" ]; then
        # Добавляем peer в конец конфига
        cat >> /etc/wireguard/wg0.conf << EOF

# Peer добавлен автоматически
[Peer]
PublicKey = $PUBLIC_KEY
AllowedIPs = $IP_ADDRESS/32
EOF
        echo "✅ Peer добавлен в конфигурационный файл"
        echo "⚠️ После перезапуска WireGuard peer будет автоматически загружен"
    else
        echo "❌ Файл /etc/wireguard/wg0.conf не найден!"
    fi
fi

