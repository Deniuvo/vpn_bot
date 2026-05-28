#!/bin/bash
# Быстрое копирование только необходимых файлов на сервер
# Использование: ./quick_copy.sh user@server

if [ -z "$1" ]; then
    echo "Использование: ./quick_copy.sh user@server"
    echo "Пример: ./quick_copy.sh root@192.168.1.100"
    exit 1
fi

SERVER=$1

echo "📦 Быстрое копирование файлов на сервер $SERVER..."
echo ""

# Создаем временную директорию
TEMP_DIR=$(mktemp -d 2>/dev/null || echo "/tmp/vpn_bot_$$")
mkdir -p "$TEMP_DIR/vpn_bot"

echo "📋 Копирование необходимых файлов..."

# Список файлов для копирования
files=(
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

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/vpn_bot/" 2>/dev/null && echo "  ✅ $file" || echo "  ⚠️  $file (ошибка)"
    else
        echo "  ❌ $file не найден"
    fi
done

echo ""
echo "🚀 Копирование на сервер..."

# Проверяем наличие scp
if ! command -v scp &> /dev/null; then
    echo "❌ scp не найден. Установите OpenSSH клиент"
    exit 1
fi

scp -r "$TEMP_DIR/vpn_bot" "${SERVER}:/root/" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Файлы успешно скопированы на сервер!"
    echo ""
    echo "📋 Проверьте на сервере:"
    echo "   ssh $SERVER"
    echo "   cd /root/vpn_bot"
    echo "   ls -la setup_wireguard.sh"
else
    echo ""
    echo "❌ Ошибка копирования. Возможные причины:"
    echo "   - Неверный адрес сервера"
    echo "   - SSH недоступен"
    echo "   - Неверный пароль/ключ"
    echo ""
    echo "Попробуйте скопировать вручную через WinSCP или другой SFTP клиент"
fi

# Очистка
rm -rf "$TEMP_DIR" 2>/dev/null

