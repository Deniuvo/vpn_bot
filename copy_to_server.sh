#!/bin/bash
# Скрипт для копирования файлов VPN бота на сервер
# Использование: ./copy_to_server.sh [user@server]

set -e

if [ -z "$1" ]; then
    echo "Использование: ./copy_to_server.sh user@server"
    echo "Пример: ./copy_to_server.sh root@192.168.1.100"
    echo ""
    echo "Или укажите параметры:"
    read -p "IP адрес сервера: " SERVER_IP
    read -p "Пользователь (по умолчанию root): " SERVER_USER
    SERVER_USER=${SERVER_USER:-root}
    SERVER="${SERVER_USER}@${SERVER_IP}"
else
    SERVER="$1"
fi

echo "📦 Копирование файлов VPN бота на сервер $SERVER..."
echo ""

# Список необходимых файлов
FILES=(
    "bot.py"
    "main.py"
    "database.py"
    "wireguard.py"
    "config_server.py"
    "yoomoney_api.py"
    "yoomoney_oauth.py"
    "setup_server.py"
    "setup_wireguard.sh"
    "setup.sh"
    "start_bot.sh"
    "requirements.txt"
    "wireguard_server_example.conf"
    "config.example.py"
)

# Создаем временную директорию для копирования
TEMP_DIR=$(mktemp -d)
echo "📁 Создание временной директории: $TEMP_DIR"

mkdir -p "$TEMP_DIR/vpn_bot"

# Копируем необходимые файлы
echo "📋 Копирование файлов..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/vpn_bot/"
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file не найден (пропущен)"
    fi
done

# Копируем директорию на сервер
echo ""
echo "🚀 Копирование на сервер..."
scp -r "$TEMP_DIR/vpn_bot" "${SERVER}:/root/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Файлы успешно скопированы!"
    echo ""
    echo "📋 Следующие шаги:"
    echo ""
    echo "1. Подключитесь к серверу:"
    echo "   ssh $SERVER"
    echo ""
    echo "2. Перейдите в директорию:"
    echo "   cd /root/vpn_bot"
    echo ""
    echo "3. Установите зависимости:"
    echo "   python3 -m venv vpn_env"
    echo "   source vpn_env/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "4. Установите WireGuard:"
    echo "   sudo bash setup_wireguard.sh"
    echo ""
    echo "5. Настройте переменные окружения и запустите бота"
    echo ""
else
    echo ""
    echo "❌ Ошибка копирования файлов!"
    echo "Проверьте:"
    echo "  - SSH подключение работает"
    echo "  - Правильность адреса сервера"
    echo "  - Права доступа"
fi

# Очистка временной директории
rm -rf "$TEMP_DIR"
echo "🧹 Временная директория удалена"

