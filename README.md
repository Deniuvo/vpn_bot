# VPN Telegram Bot

Telegram бот для продажи VPN услуг через WireGuard.

## Возможности

- 🛒 Покупка VPN подписок (1 месяц, 3 месяца, 1 год)
- 💳 **Автоматическая проверка платежей через API ЮMoney**
- 🔐 Автоматическая генерация WireGuard конфигов
- 📱 Поддержка iOS, Android, Windows, macOS
- 💾 SQLite база данных для хранения пользователей
- 🌐 HTTP сервер для раздачи конфигов
- ⚙️ Автоматическое добавление peers на WireGuard сервер
- 📸 Резервный метод проверки через скриншоты (если API не настроен)

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка WireGuard сервера

Убедитесь, что WireGuard установлен и настроен на вашем сервере:

```bash
# Установка WireGuard (Ubuntu/Debian)
sudo apt update
sudo apt install wireguard wireguard-tools

# Создание конфигурации сервера
sudo wg genkey | sudo tee /etc/wireguard/private.key
sudo cat /etc/wireguard/private.key | sudo wg pubkey | sudo tee /etc/wireguard/public.key

# Настройка интерфейса wg0 (пример)
# /etc/wireguard/wg0.conf:
# [Interface]
# PrivateKey = <сервер_приватный_ключ>
# Address = 10.0.0.1/24
# ListenPort = 51820
# PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Запуск WireGuard
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0
```

### 3. Настройка переменных окружения

Отредактируйте файл `bot.py` и укажите:

- `SERVER_IP` - IP адрес вашего сервера
- `SERVER_PUBLIC_KEY` (опционально) - публичный ключ сервера (будет определен автоматически)
- `YMONEY_ACCESS_TOKEN` - токен доступа к API ЮMoney для автоматической проверки платежей

Или установите через переменные окружения:

```bash
export SERVER_IP="your_server_ip"
export SERVER_PUBLIC_KEY="your_server_public_key"  # опционально
export YMONEY_ACCESS_TOKEN="your_yoomoney_token"  # для автоматической проверки платежей
export USE_YOOMONEY_API="true"  # включить API проверку
```

#### Получение токена API ЮMoney:

**OAuth2 credentials уже настроены в коде:**
- `client_id`: 5DE3736B6BA71E9420E1B269CD147ACD8AEA6F69AE4FE87E5AD80983E49A2FD0
- `client_secret`: Настроен в bot.py

**Для получения access token:**

1. Установите библиотеку: `pip install yoomoney`
2. Запустите скрипт: `python yoomoney_oauth.py`
3. Откройте URL в браузере и авторизуйтесь
4. Скопируйте код из redirect URL
5. Запустите: `python yoomoney_oauth.py ВАШ_КОД`
6. Сохраните полученный токен: `export YMONEY_ACCESS_TOKEN="ваш_токен"`

Подробная инструкция: см. `GET_TOKEN.md`

**Примечание:** Если токен не указан, бот будет работать в режиме ручной проверки через скриншоты.

### 4. Настройка HTTP сервера для конфигов

#### Вариант 1: Использование Flask (для разработки)

Бот автоматически запускает Flask сервер на порту 5000.

#### Вариант 2: Использование nginx (для продакшена)

Создайте конфигурацию nginx:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location /config/ {
        alias /path/to/vpn_bot/configs/;
        default_type application/octet-stream;
        add_header Content-Disposition "attachment";
    }
}
```

И обновите `CONFIG_BASE_URL` в `bot.py`.

### 5. Запуск бота

```bash
python bot.py
```

## Структура проекта

```
vpn_bot/
├── bot.py              # Главный файл бота
├── database.py         # Работа с базой данных
├── wireguard.py        # Генерация конфигов и управление WireGuard
├── config_server.py    # HTTP сервер для раздачи конфигов
├── requirements.txt    # Зависимости Python
├── configs/           # Директория с конфигами (создается автоматически)
└── vpn_bot.db         # SQLite база данных (создается автоматически)
```

## Команды бота

- `/start` - Приветствие и главное меню
- `/buy` - Покупка VPN подписки
- `/status` - Проверка статуса VPN сервера
- `/support` - Связь с поддержкой
- `/myconfig` - Получение ссылки на конфиг

## Процесс покупки

1. Пользователь выбирает тариф (1 месяц, 3 месяца, 1 год)
2. Бот показывает реквизиты ЮMoney для оплаты
3. Пользователь отправляет скриншот чека об оплате
4. Бот автоматически генерирует WireGuard конфиг
5. Бот добавляет peer на WireGuard сервер
6. Пользователь получает ссылку на конфиг

## База данных

База данных SQLite содержит следующие таблицы:

- `users` - информация о пользователях и подписках
- `used_ips` - отслеживание использованных IP адресов

## Безопасность

⚠️ **Важно:**

1. Не храните токен бота и приватные ключи в коде (используйте переменные окружения)
2. Настройте файрвол для защиты порта 5000 (или используйте nginx с SSL)
3. Регулярно делайте резервные копии базы данных
4. ✅ **Автоматическая проверка платежей через API ЮMoney настроена** (см. `yoomoney_api.py`)
5. Используйте HTTPS для раздачи конфигов в продакшене
6. Храните токен API ЮMoney в переменных окружения, а не в коде

## Развертывание на сервере

См. подробные инструкции в файле `DEPLOY.md` или используйте команды из `commands.txt`.

Быстрый старт:

```bash
# Копирование на сервер
cd Desktop
scp -r vpn_bot root@90.156.169.27:/root/

# На сервере
ssh root@90.156.169.27
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install -r requirements.txt
python3 bot.py
```

## Разработка

Для автоматической проверки платежей можно интегрировать:

- API ЮMoney для проверки платежей
- Вебхуки для получения уведомлений об оплате
- Админ-панель для ручной проверки скриншотов

## Лицензия

MIT

