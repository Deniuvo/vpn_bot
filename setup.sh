#!/bin/bash
# Скрипт для автоматической настройки VPN бота на сервере

set -e  # Остановка при ошибке

echo "🚀 Начинаю установку VPN бота..."

# Переходим в директорию проекта
cd "$(dirname "$0")"
echo "📁 Рабочая директория: $(pwd)"

# Проверяем наличие Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python3."
    exit 1
fi

echo "✅ Python3 найден: $(python3 --version)"

# Создаем виртуальное окружение, если его нет
if [ ! -d "vpn_env" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv vpn_env
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активируем виртуальное окружение
echo "🔌 Активирую виртуальное окружение..."
source vpn_env/bin/activate

# Обновляем pip
echo "⬆️  Обновляю pip..."
pip install --upgrade pip --quiet

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    echo "📥 Устанавливаю зависимости из requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Зависимости установлены"
else
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "⚠️  ВАЖНО: Теперь нужно установить переменные окружения:"
echo ""
echo "export SERVER_IP=\"ВАШ_IP_АДРЕС_СЕРВЕРА\""
echo "export YMONEY_ACCESS_TOKEN=\"4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D\""
echo "export USE_YOOMONEY_API=\"true\""
echo ""
echo "🚀 Для запуска бота используйте:"
echo "   source vpn_env/bin/activate"
echo "   python3 main.py"
echo ""

