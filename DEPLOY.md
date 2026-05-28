# Инструкция по развертыванию VPN бота на сервере

## Команды для деплоя

### 1. Копирование файлов на сервер

С вашего локального компьютера (из директории Desktop):

```bash
cd Desktop
scp -r vpn_bot root@90.156.169.27:/root/
```

Замените `90.156.169.27` на IP адрес вашего сервера.

### 2. Подключение к серверу

```bash
ssh root@90.156.169.27
```

### 3. Переход в директорию бота

```bash
cd /root/vpn_bot
```

### 4. Создание виртуального окружения

```bash
python3 -m venv vpn_env
```

### 5. Активация виртуального окружения

```bash
source vpn_env/bin/activate
```

### 6. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 7. Настройка переменных окружения

Создайте файл `.env` или экспортируйте переменные:

```bash
export SERVER_IP="ваш_ip_адрес"
export SERVER_PUBLIC_KEY="ваш_публичный_ключ"  # опционально
export YMONEY_ACCESS_TOKEN="ваш_токен_юmoney"  # для автоматической проверки платежей
export USE_YOOMONEY_API="true"
```

Или отредактируйте `bot.py` напрямую, заменив значения.

### 8. Запуск бота

```bash
python3 bot.py
```

## Запуск в фоновом режиме

### Вариант 1: Использование screen

```bash
# Установка screen (если не установлен)
apt install screen -y

# Создание новой сессии
screen -S vpn_bot

# Активация окружения и запуск
cd /root/vpn_bot
source vpn_env/bin/activate
python3 bot.py

# Выход из screen (не останавливая бота): Ctrl+A, затем D
# Вернуться в сессию: screen -r vpn_bot
```

### Вариант 2: Использование systemd (рекомендуется)

Создайте файл `/etc/systemd/system/vpn-bot.service`:

```ini
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vpn_bot
Environment="PATH=/root/vpn_bot/vpn_env/bin"
ExecStart=/root/vpn_bot/vpn_env/bin/python3 /root/vpn_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable vpn-bot

# Запуск сервиса
systemctl start vpn-bot

# Проверка статуса
systemctl status vpn-bot

# Просмотр логов
journalctl -u vpn-bot -f
```

### Вариант 3: Использование nohup

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
nohup python3 bot.py > bot.log 2>&1 &
```

## Настройка WireGuard сервера

### 1. Установка WireGuard

```bash
apt update
apt install wireguard wireguard-tools -y
```

### 2. Генерация ключей сервера

```bash
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key
chmod 600 /etc/wireguard/private.key
```

### 3. Настройка интерфейса

Создайте файл `/etc/wireguard/wg0.conf` (см. `wireguard_server_example.conf`)

### 4. Включение IP forwarding

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

### 5. Запуск WireGuard

```bash
wg-quick up wg0
systemctl enable wg-quick@wg0
```

### 6. Настройка файрвола

```bash
# Разрешить WireGuard порт
ufw allow 51820/udp

# Разрешить HTTP порт для конфигов
ufw allow 5000/tcp

# Или для nginx
ufw allow 80/tcp
ufw allow 443/tcp
```

## Настройка nginx (опционально, для продакшена)

### 1. Установка nginx

```bash
apt install nginx -y
```

### 2. Создание конфигурации

Создайте файл `/etc/nginx/sites-available/vpn-bot`:

```nginx
server {
    listen 80;
    server_name your_domain.com;  # или IP адрес

    location /config/ {
        alias /root/vpn_bot/configs/;
        default_type application/octet-stream;
        add_header Content-Disposition "attachment";
        
        # Безопасность (опционально)
        # allow 192.168.1.0/24;
        # deny all;
    }
}
```

### 3. Активация конфигурации

```bash
ln -s /etc/nginx/sites-available/vpn-bot /etc/nginx/sites-enabled/
nginx -t  # проверка конфигурации
systemctl reload nginx
```

### 4. Обновление CONFIG_BASE_URL в bot.py

```python
CONFIG_BASE_URL = f"http://your_domain.com/config"  # или через IP
```

## Получение токена API ЮMoney

1. Перейдите на https://yoomoney.ru/
2. Войдите в аккаунт
3. Перейдите в раздел "Для разработчиков"
4. Создайте приложение и получите токен доступа
5. Установите токен:

```bash
export YMONEY_ACCESS_TOKEN="ваш_токен"
```

## Мониторинг и логи

### Просмотр логов бота

Если используете systemd:
```bash
journalctl -u vpn-bot -f
```

Если используете nohup:
```bash
tail -f /root/vpn_bot/bot.log
```

### Проверка статуса WireGuard

```bash
wg show
```

### Проверка базы данных

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 -c "from database import db; import sqlite3; conn = sqlite3.connect('vpn_bot.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM users'); print(cursor.fetchall())"
```

## Резервное копирование

### Копирование базы данных

```bash
# На сервере
cd /root/vpn_bot
cp vpn_bot.db vpn_bot.db.backup

# Копирование на локальный компьютер
scp root@90.156.169.27:/root/vpn_bot/vpn_bot.db.backup ~/Desktop/
```

### Копирование конфигов

```bash
# Создание архива
tar -czf configs_backup.tar.gz configs/

# Копирование на локальный компьютер
scp root@90.156.169.27:/root/vpn_bot/configs_backup.tar.gz ~/Desktop/
```

## Обновление бота

```bash
# На локальном компьютере
cd Desktop/vpn_bot
# Внесите изменения в код

# Копирование обновленного кода
scp -r vpn_bot root@90.156.169.27:/root/vpn_bot_new

# На сервере
cd /root/vpn_bot_new
source vpn_env/bin/activate
pip install -r requirements.txt

# Остановка старого бота
systemctl stop vpn-bot  # если используете systemd
# или
pkill -f "python3 bot.py"

# Замена директории
cd /root
mv vpn_bot vpn_bot_old
mv vpn_bot_new vpn_bot

# Копирование базы данных
cp vpn_bot_old/vpn_bot.db vpn_bot/
cp -r vpn_bot_old/configs vpn_bot/

# Запуск нового бота
cd /root/vpn_bot
source vpn_env/bin/activate
systemctl start vpn-bot  # или python3 bot.py
```

## Полная последовательность команд (быстрый старт)

```bash
# 1. На локальном компьютере
cd Desktop
scp -r vpn_bot root@90.156.169.27:/root/

# 2. На сервере
ssh root@90.156.169.27
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install -r requirements.txt

# 3. Настройка (отредактируйте bot.py или экспортируйте переменные)
export SERVER_IP="ваш_ip"
export YMONEY_ACCESS_TOKEN="ваш_токен"

# 4. Запуск
python3 bot.py
```

## Решение проблем

### Бот не запускается

```bash
# Проверка Python
python3 --version

# Проверка зависимостей
source vpn_env/bin/activate
pip list

# Проверка токена бота
grep BOT_TOKEN bot.py
```

### WireGuard не работает

```bash
# Проверка статуса
systemctl status wg-quick@wg0

# Проверка интерфейса
ip addr show wg0

# Проверка подключений
wg show
```

### База данных заблокирована

```bash
# Остановка бота
systemctl stop vpn-bot

# Проверка блокировок
lsof vpn_bot.db

# Резервная копия и восстановление
cp vpn_bot.db vpn_bot.db.backup
sqlite3 vpn_bot.db ".recover" | sqlite3 vpn_bot_recovered.db
```

