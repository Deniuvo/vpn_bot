#!/bin/bash
# Скрипт для автоматического развертывания VPN бота на сервере

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Развертывание VPN бота на сервере ===${NC}\n"

# Параметры
SERVER_IP="${1:-90.156.169.27}"
SERVER_USER="${2:-root}"
PROJECT_DIR="/root/vpn_bot"
VENV_NAME="vpn_env"

# Проверка аргументов
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Использование: ./deploy.sh [SERVER_IP] [USER]"
    echo "Пример: ./deploy.sh 90.156.169.27 root"
    exit 0
fi

echo -e "${YELLOW}Сервер: ${SERVER_USER}@${SERVER_IP}${NC}"
echo -e "${YELLOW}Директория: ${PROJECT_DIR}${NC}\n"

# Шаг 1: Копирование файлов
echo -e "${GREEN}[1/7] Копирование файлов на сервер...${NC}"
scp -r vpn_bot ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка копирования файлов!${NC}"
    exit 1
fi

# Шаг 2-7: Выполнение на сервере
echo -e "${GREEN}[2/7] Подключение к серверу и настройка...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    set -e
    
    cd ${PROJECT_DIR}
    
    # Создание виртуального окружения
    echo "[3/7] Создание виртуального окружения..."
    python3 -m venv ${VENV_NAME} || python3 -m venv --clear ${VENV_NAME}
    
    # Активация и установка зависимостей
    echo "[4/7] Установка зависимостей..."
    source ${VENV_NAME}/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Создание директорий
    echo "[5/7] Создание необходимых директорий..."
    mkdir -p configs
    
    # Проверка файлов
    echo "[6/7] Проверка конфигурации..."
    if ! grep -q "YOUR_SERVER_IP" bot.py 2>/dev/null; then
        echo "✓ IP сервера настроен"
    else
        echo "⚠ ВНИМАНИЕ: Необходимо настроить SERVER_IP в bot.py"
    fi
    
    echo "[7/7] Готово!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Подключитесь к серверу: ssh ${SERVER_USER}@${SERVER_IP}"
    echo "2. Перейдите в директорию: cd ${PROJECT_DIR}"
    echo "3. Активируйте окружение: source ${VENV_NAME}/bin/activate"
    echo "4. Настройте переменные окружения или отредактируйте bot.py:"
    echo "   export SERVER_IP=\"ваш_ip\""
    echo "   export YMONEY_ACCESS_TOKEN=\"ваш_токен\""
    echo "5. Запустите бота: python3 bot.py"
    echo ""
    echo "Или используйте systemd для автозапуска (см. DEPLOY.md)"

EOF

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Развертывание завершено успешно!${NC}"
else
    echo -e "\n${RED}✗ Произошла ошибка при развертывании${NC}"
    exit 1
fi

