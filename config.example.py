"""
Пример конфигурационного файла
Скопируйте этот файл как config.py и заполните своими данными
НЕ КОММИТЬТЕ config.py в репозиторий!
"""

# Токен Telegram бота
BOT_TOKEN = "8975004514:AAGCCRTwuIFBI5d5Pn2ZByJJplGGxHIOL2M"

# Контакты поддержки
SUPPORT_USERNAME = "@deniuvo"

# Реквизиты для оплаты (номер кошелька ЮMoney)
YMONEY_WALLET = "4100119393589473"

# OAuth2 приложение «Сойка VPN» (кабинет ЮMoney)
YOOMONEY_CLIENT_ID = "FF72E621F882081F4C017BD0F74C63EB9E5E731C4F40D104EEF5C9712D33188C"
YOOMONEY_CLIENT_SECRET = "FB797ECE763B9291838B433CCDCC7030C735EF5AB15F6B06498A3CA4975E49A63B8FA03523B80DA38ABD06661BBA82F68EADE81DD776CE1B84B27A00CF808AF2"
# Токен получается один раз: python yoomoney_oauth.py (см. YOOMONEY_SOYKA_VPN.md)
# YMONEY_ACCESS_TOKEN = "ваш_токен_после_oauth"
# USE_YOOMONEY_API = "true"

# Настройки сервера
SERVER_IP = "YOUR_SERVER_IP"  # Замените на реальный IP
SERVER_PUBLIC_KEY = None  # Опционально, публичный ключ WireGuard сервера

# URL для раздачи конфигов
CONFIG_BASE_URL = f"http://{SERVER_IP}:5000/config"  # Или через nginx с доменом

# Настройки WireGuard
WG_INTERFACE = "wg0"  # Имя интерфейса WireGuard

# Диапазон IP адресов для клиентов
CLIENT_IP_RANGE = "10.0.0.2-10.0.0.254"

# DNS сервер для клиентов
CLIENT_DNS = "8.8.8.8"

# Порт WireGuard
WG_PORT = 51820

# Тарифы
TARIFFS = {
    "1_month": {"name": "1 месяц", "price": 90, "days": 30},
    "3_months": {"name": "3 месяца", "price": 250, "days": 90},
    "1_year": {"name": "1 год", "price": 800, "days": 365}
}

# ID чата администратора для уведомлений (опционально)
# ADMIN_CHAT_ID = 123456789

# Настройки HTTP сервера для конфигов
CONFIG_SERVER_HOST = "0.0.0.0"
CONFIG_SERVER_PORT = 5000

