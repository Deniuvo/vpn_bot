#!/bin/bash
# Скрипт для автоматической установки VPN бота на удаленном сервере через SSH
# Выполняет все необходимые команды автоматически

set -e  # Остановка при ошибке

echo "🚀 Автоматическая установка VPN бота на сервере через SSH"
echo "=========================================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Запрос данных подключения
echo "📋 Введите данные для подключения к серверу:"
read -p "IP адрес сервера: " SERVER_IP_ADDR
read -p "Пользователь (обычно root): " SSH_USER
SSH_USER=${SSH_USER:-root}

echo ""
echo "Выберите метод аутентификации:"
echo "1) По паролю (требует sshpass)"
echo "2) По SSH ключу (рекомендуется)"
read -p "Ваш выбор (1 или 2): " AUTH_METHOD

SSH_CMD="ssh"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

if [ "$AUTH_METHOD" == "1" ]; then
    # Проверка наличия sshpass
    if ! command -v sshpass &> /dev/null; then
        echo -e "${RED}❌ sshpass не установлен${NC}"
        echo "Установите: sudo apt install sshpass (Linux) или brew install sshpass (Mac)"
        exit 1
    fi
    read -sp "Пароль: " SSH_PASS
    echo ""
    SSH_CMD="sshpass -p '$SSH_PASS' ssh"
elif [ "$AUTH_METHOD" == "2" ]; then
    read -p "Путь к SSH ключу (пусто = использовать ~/.ssh/id_rsa): " SSH_KEY
    SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}
    if [ -f "$SSH_KEY" ]; then
        SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
    else
        echo -e "${YELLOW}⚠️  Файл ключа не найден, будет использован стандартный ключ${NC}"
    fi
else
    echo -e "${RED}❌ Неверный выбор${NC}"
    exit 1
fi

# Функция выполнения команды на сервере
execute_remote() {
    local cmd="$1"
    local description="$2"
    
    if [ -n "$description" ]; then
        echo -e "\n${GREEN}▶ $description${NC}"
    fi
    
    eval "$SSH_CMD $SSH_OPTS $SSH_USER@$SERVER_IP_ADDR '$cmd'"
    
    if [ $? -eq 0 ]; then
        return 0
    else
        echo -e "${RED}❌ Ошибка выполнения команды${NC}"
        return 1
    fi
}

# Тест подключения
echo ""
echo -e "${YELLOW}🔌 Проверка подключения к серверу...${NC}"
if eval "$SSH_CMD $SSH_OPTS $SSH_USER@$SERVER_IP_ADDR 'echo \"Подключение успешно\"'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Подключение успешно!${NC}"
else
    echo -e "${RED}❌ Не удалось подключиться к серверу${NC}"
    echo "Проверьте:"
    echo "  - IP адрес правильный"
    echo "  - Пользователь существует"
    echo "  - SSH сервис запущен на сервере"
    echo "  - Пароль/ключ правильный"
    exit 1
fi

echo ""
echo "=========================================================="
echo "Начинаю установку..."
echo "=========================================================="

# 1. Создание директории и копирование файлов (если нужно)
echo -e "\n${GREEN}📁 Шаг 1: Проверка директории проекта${NC}"
execute_remote "mkdir -p /root/vpn_bot" "Создание директории"

# 2. Установка зависимостей Python
echo -e "\n${GREEN}🐍 Шаг 2: Установка Python и зависимостей${NC}"
execute_remote "cd /root/vpn_bot && if [ ! -d 'vpn_env' ]; then python3 -m venv vpn_env; fi" "Создание виртуального окружения"
execute_remote "cd /root/vpn_bot && source vpn_env/bin/activate && pip install --upgrade pip --quiet && pip install -r requirements.txt" "Установка зависимостей"

# 3. Установка и настройка WireGuard
echo -e "\n${GREEN}🔐 Шаг 3: Установка и настройка WireGuard${NC}"
execute_remote "cd /root/vpn_bot && sudo bash setup_wireguard.sh" "Установка WireGuard"

# 4. Получение данных для переменных окружения
echo -e "\n${GREEN}📋 Шаг 4: Получение данных сервера${NC}"
SERVER_DATA=$(execute_remote "cd /root/vpn_bot && source vpn_env/bin/activate && python3 setup_server.py 2>/dev/null | grep -E 'Публичный IP|Публичный ключ' || echo ''" "Получение данных")

echo "$SERVER_DATA"

# 5. Настройка переменных окружения
echo -e "\n${GREEN}⚙️  Шаг 5: Настройка переменных окружения${NC}"

# Получаем публичный IP
PUBLIC_IP=$(execute_remote "curl -s ifconfig.me || curl -s ipinfo.io/ip" "Получение публичного IP")

# Получаем публичный ключ WireGuard
WG_PUBLIC_KEY=$(execute_remote "sudo wg show wg0 public-key 2>/dev/null || sudo cat /etc/wireguard/public.key 2>/dev/null || echo ''" "Получение публичного ключа WireGuard")

# Токен ЮMoney (из файла или переменной)
YMONEY_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"

# Установка переменных в ~/.bashrc
execute_remote "
echo '' >> ~/.bashrc
echo '# VPN Bot Environment Variables' >> ~/.bashrc
echo 'export SERVER_IP=\"$PUBLIC_IP\"' >> ~/.bashrc
echo 'export SERVER_PUBLIC_KEY=\"$WG_PUBLIC_KEY\"' >> ~/.bashrc
echo 'export YMONEY_ACCESS_TOKEN=\"$YMONEY_TOKEN\"' >> ~/.bashrc
echo 'export USE_YOOMONEY_API=\"true\"' >> ~/.bashrc
" "Добавление переменных в ~/.bashrc"

# Применение переменных в текущей сессии
execute_remote "
export SERVER_IP=\"$PUBLIC_IP\"
export SERVER_PUBLIC_KEY=\"$WG_PUBLIC_KEY\"
export YMONEY_ACCESS_TOKEN=\"$YMONEY_TOKEN\"
export USE_YOOMONEY_API=\"true\"
" "Установка переменных окружения"

# 6. Проверка настроек
echo -e "\n${GREEN}✅ Шаг 6: Проверка настроек${NC}"
execute_remote "echo \"SERVER_IP: \$SERVER_IP\"" "Проверка SERVER_IP"
execute_remote "echo \"SERVER_PUBLIC_KEY: \$SERVER_PUBLIC_KEY\"" "Проверка SERVER_PUBLIC_KEY"
execute_remote "sudo wg show" "Проверка WireGuard"

echo ""
echo "=========================================================="
echo -e "${GREEN}✅ УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo "=========================================================="
echo ""
echo "📋 Установленные значения:"
echo "   SERVER_IP: $PUBLIC_IP"
echo "   SERVER_PUBLIC_KEY: $WG_PUBLIC_KEY"
echo ""
echo "🚀 Для запуска бота выполните на сервере:"
echo ""
echo "   ssh $SSH_USER@$SERVER_IP_ADDR"
echo "   cd /root/vpn_bot"
echo "   source vpn_env/bin/activate"
echo "   python3 main.py"
echo ""
echo "📖 Или используйте systemd для автозапуска (см. DEPLOY.md)"
echo ""
echo -e "${GREEN}Готово! Бот готов к запуску! 🎉${NC}"

