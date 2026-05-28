#!/bin/bash
# Быстрое создание директории для Shadowsocks

echo "🔧 Создание директории для Shadowsocks..."

# Создаем директорию
sudo mkdir -p /etc/shadowsocks-libev

# Устанавливаем права
sudo chmod 755 /etc/shadowsocks-libev

echo "✅ Директория /etc/shadowsocks-libev/ создана!"

echo ""
echo "Теперь можно создать конфиг:"
echo "sudo nano /etc/shadowsocks-libev/config.json"

