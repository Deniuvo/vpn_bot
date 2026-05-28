#!/bin/bash
# Скрипт для обновления yoomoney_api.py на сервере
# Использование: bash update_yoomoney_api.sh user@server

if [ -z "$1" ]; then
    echo "Использование: bash update_yoomoney_api.sh user@server"
    echo "Пример: bash update_yoomoney_api.sh root@192.168.1.100"
    exit 1
fi

SERVER=$1

echo "📦 Копирование yoomoney_api.py на сервер $SERVER..."

if [ ! -f "yoomoney_api.py" ]; then
    echo "❌ Файл yoomoney_api.py не найден в текущей директории!"
    exit 1
fi

scp yoomoney_api.py "${SERVER}:/root/vpn_bot/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ yoomoney_api.py успешно обновлен на сервере!"
    echo ""
    echo "🔄 Перезапустите бота на сервере:"
    echo "   ssh $SERVER"
    echo "   cd /root/vpn_bot"
    echo "   pkill -f 'python3 main.py'"
    echo "   bash start_bot.sh"
else
    echo ""
    echo "❌ Ошибка копирования файла!"
    echo "Проверьте подключение к серверу"
fi

