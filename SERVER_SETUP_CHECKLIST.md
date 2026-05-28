# ✅ Чек-лист настройки на сервере

## ⚡ БЫСТРОЕ РЕШЕНИЕ: Полная настройка с нуля

**Если бот не запускается или нужно настроить всё с нуля:**

### Шаг 0: ⚠️ СНАЧАЛА: Скопируйте файлы на сервер

**Если вы видите ошибку "No such file or directory" при запуске скриптов - файлы еще не скопированы!**

```bash
# С вашего компьютера (Linux/Mac)
cd ~/Desktop/vpn_bot
scp -r . root@ваш_сервер:/root/vpn_bot

# Или используйте автоматический скрипт
chmod +x copy_to_server.sh
./copy_to_server.sh root@ваш_сервер
```

**Для Windows:** Используйте WinSCP (см. `COPY_TO_SERVER.md`)

**Проверка:**
```bash
ssh root@ваш_сервер
cd /root/vpn_bot
ls -la setup_wireguard.sh  # Должен существовать!
```

📖 **Подробнее:** См. `COPY_FILES_TO_SERVER.md`

---

### Шаг 1: Установка зависимостей Python

```bash
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 2: Установка и настройка WireGuard

```bash
# Автоматическая установка (рекомендуется)
sudo bash setup_wireguard.sh

# Скрипт покажет публичный IP и ключ WireGuard - сохраните их!
```

### Шаг 3: Настройка переменных окружения

После установки WireGuard выполните:

```bash
# Получаем данные автоматически
cd /root/vpn_bot
source vpn_env/bin/activate
python3 setup_server.py

# Или устанавливаем вручную (замените значения!)
export SERVER_IP="ВАШ_ПУБЛИЧНЫЙ_IP"
export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ_WIREGUARD"
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="true"
```

### Шаг 4: Запуск бота

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py
```

---

## ⚡ БЫСТРОЕ РЕШЕНИЕ: Если бот не запускается (только ошибки Python)

Если вы видите ошибки:
- `No such file or directory` при `source vpn_env/bin/activate`
- `ModuleNotFoundError: No module named 'telegram'`
- `ОШИБКА: Не настроен IP сервера`

**Выполните эти команды по порядку:**

```bash
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export SERVER_IP="ВАШ_IP_АДРЕС_СЕРВЕРА"
export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ_WIREGUARD"
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="true"
python3 main.py
```

---

## 🚀 Что нужно сделать на сервере перед запуском:

### 1. ✅ Установить зависимости Python

**ВАРИАНТ А: Автоматическая установка (рекомендуется)**

```bash
cd /root/vpn_bot
bash setup.sh
```

**ВАРИАНТ Б: Ручная установка**

```bash
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**⚠️ Если видите ошибку "No such file or directory"** - это значит виртуальное окружение не создано. Выполните команды выше.

---

### 2. ⚠️ КРИТИЧНО: Настроить переменные окружения

**Обязательные переменные:**

```bash
export SERVER_IP="ВАШ_ПУБЛИЧНЫЙ_IP_АДРЕС_СЕРВЕРА"
export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ_WIREGUARD"  # Опционально, но рекомендуется
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="true"
```

**Как получить значения:**

```bash
# Автоматический способ (после установки WireGuard)
cd /root/vpn_bot
source vpn_env/bin/activate
python3 setup_server.py

# Ручной способ - публичный IP
curl ifconfig.me

# Ручной способ - публичный ключ WireGuard
sudo wg show wg0 public-key
# или
sudo cat /etc/wireguard/public.key
```

**Для постоянного сохранения** добавьте в `~/.bashrc` или `~/.profile`:

```bash
echo 'export SERVER_IP="ВАШ_IP"' >> ~/.bashrc
echo 'export SERVER_PUBLIC_KEY="ВАШ_КЛЮЧ_WIREGUARD"' >> ~/.bashrc
echo 'export YMONEY_ACCESS_TOKEN="ваш_токен"' >> ~/.bashrc
echo 'export USE_YOOMONEY_API="true"' >> ~/.bashrc
source ~/.bashrc
```

---

### 3. ✅ Настроить WireGuard (если еще не настроен)

**📖 Полная инструкция:** См. файл `WIREGUARD_SETUP.md` для детальной настройки.

**ВАРИАНТ А: Автоматическая установка (рекомендуется)**

```bash
# Запуск автоматического скрипта установки
cd /root/vpn_bot
sudo bash setup_wireguard.sh
```

Скрипт автоматически:
- Установит WireGuard
- Сгенерирует ключи
- Создаст конфигурацию
- Настроит IP forwarding
- Откроет порты
- Запустит WireGuard
- Покажет данные для настройки бота

**ВАРИАНТ Б: Ручная установка**

Следуйте подробной инструкции в файле `WIREGUARD_SETUP.md` или выполните:

```bash
# Установка
sudo apt update
sudo apt install wireguard wireguard-tools -y

# Генерация ключей
cd /etc/wireguard
sudo wg genkey | sudo tee private.key
sudo chmod 600 private.key
sudo cat private.key | sudo wg pubkey | sudo tee public.key

# Включение IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Открытие портов
sudo ufw allow 51820/udp
sudo ufw allow 5000/tcp

# Создание конфигурации (отредактируйте после создания!)
sudo nano /etc/wireguard/wg0.conf

# Запуск
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0

# Проверка
sudo wg show
```

**⚠️ После установки WireGuard получите данные для бота:**

```bash
# Получить публичный IP и ключ
cd /root/vpn_bot
source vpn_env/bin/activate
python3 setup_server.py
```

---

### 4. ✅ Открыть порты в файрволе

```bash
# Порт 51820 для WireGuard
sudo ufw allow 51820/udp

# Порт 5000 для HTTP сервера конфигов
sudo ufw allow 5000/tcp

# Или для iptables:
sudo iptables -A INPUT -p udp --dport 51820 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

---

### 5. ✅ Проверить, что база данных создастся

База данных SQLite создастся автоматически при первом запуске в файле `database.db`.

---

### 6. ✅ Запустить бота

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py
```

**Или можно использовать bot.py напрямую:**

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 bot.py
```

**Для фонового режима с screen:**

```bash
screen -S vpn_bot
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py
# Выход: Ctrl+A, затем D
```

**⚠️ Помните:** Всегда активируйте виртуальное окружение (`source vpn_env/bin/activate`) перед запуском!

---

### 7. ✅ (Опционально) Настроить автозапуск через systemd

Создайте файл `/etc/systemd/system/vpn-bot.service`:

```ini
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vpn_bot
Environment="SERVER_IP=ВАШ_IP"
Environment="YMONEY_ACCESS_TOKEN=ваш_токен"
Environment="USE_YOOMONEY_API=true"
ExecStart=/root/vpn_bot/vpn_env/bin/python3 /root/vpn_bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vpn-bot
sudo systemctl start vpn-bot
sudo systemctl status vpn-bot
```

---

## 📋 Проверка перед запуском:

- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] `SERVER_IP` установлен (критично!)
- [ ] `YMONEY_ACCESS_TOKEN` установлен
- [ ] WireGuard установлен и работает
- [ ] Порты открыты (51820 UDP, 5000 TCP)
- [ ] Бот запускается без ошибок

---

## ⚠️ Важно:

1. **SERVER_IP** - без этого бот не запустится! Бот проверит это при старте.
2. **Токен ЮMoney** - уже получен, нужно только установить на сервере
3. **WireGuard** - должен быть настроен и работать
4. **Порты** - должны быть открыты для работы VPN и раздачи конфигов

---

## 🎯 Итого, на сервере нужно:

1. ✅ Установить зависимости
2. ✅ Установить переменные окружения (особенно SERVER_IP!)
3. ✅ Настроить WireGuard (если еще не настроен)
4. ✅ Открыть порты в файрволе
5. ✅ Запустить бота

**Все остальное уже готово!** 🚀

