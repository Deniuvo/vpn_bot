# 🚀 Быстрый старт: Настройка VPN бота на сервере

Краткая пошаговая инструкция для быстрого запуска бота.

---

## ⚡ Быстрая установка (5 минут)

### 0. ⚠️ СНАЧАЛА: Скопируйте файлы на сервер

**Если файлов еще нет на сервере:**

```bash
# С вашего компьютера (Linux/Mac)
cd ~/Desktop/vpn_bot
scp -r . root@ваш_сервер:/root/vpn_bot

# Или используйте автоматический скрипт
chmod +x copy_to_server.sh
./copy_to_server.sh root@ваш_сервер
```

**Для Windows:** Используйте WinSCP (см. `COPY_TO_SERVER.md`)

**Проверьте, что файлы скопированы:**
```bash
ssh root@ваш_сервер
cd /root/vpn_bot
ls -la setup_wireguard.sh  # Должен существовать
```

---

### 1. Установите зависимости Python

```bash
cd /root/vpn_bot
python3 -m venv vpn_env
source vpn_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Установите и настройте WireGuard

```bash
sudo bash setup_wireguard.sh
```

**Скрипт автоматически:**
- ✅ Установит WireGuard
- ✅ Сгенерирует ключи
- ✅ Настроит конфигурацию
- ✅ **Добавит защиту SSH** (предотвратит закрытие доступа к серверу)
- ✅ Откроет порты
- ✅ Запустит WireGuard

**⚠️ Защита SSH:** Скрипт автоматически настроит правила, которые гарантируют, что SSH трафик всегда идет через основной интерфейс, а НЕ через WireGuard. Это предотвратит закрытие доступа к серверу.

**Важно:** После выполнения скрипт покажет:
- Публичный IP сервера
- Публичный ключ WireGuard

**Сохраните эти данные!**

**📖 Подробнее о защите SSH:** См. `SSH_PROTECTION.md`

### 3. Настройте переменные окружения

```bash
# Автоматически получить данные
source vpn_env/bin/activate
python3 setup_server.py

# Или установите вручную (замените значения!)
export SERVER_IP="ВАШ_ПУБЛИЧНЫЙ_IP"
export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ"
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="true"

# Для постоянного сохранения
echo 'export SERVER_IP="ВАШ_IP"' >> ~/.bashrc
echo 'export SERVER_PUBLIC_KEY="ВАШ_КЛЮЧ"' >> ~/.bashrc
echo 'export YMONEY_ACCESS_TOKEN="ваш_токен"' >> ~/.bashrc
echo 'export USE_YOOMONEY_API="true"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Запустите бота

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py
```

**Готово!** Бот запущен и готов принимать заказы! 🎉

---

## 📋 Проверка работы

### Проверить WireGuard:

```bash
sudo wg show
```

Должен показать интерфейс `wg0` с портом 51820.

### Проверить переменные окружения:

```bash
echo $SERVER_IP
echo $SERVER_PUBLIC_KEY
```

Должны показать ваши значения.

### Проверить работу бота:

Откройте Telegram и найдите вашего бота. Отправьте команду `/start`.

---

## 🔧 Если что-то не работает

### Бот не запускается

1. **Проверьте виртуальное окружение:**
   ```bash
   source vpn_env/bin/activate
   ```

2. **Проверьте зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Проверьте переменные окружения:**
   ```bash
   echo $SERVER_IP  # Должно показать ваш IP
   ```

### WireGuard не работает

1. **Проверьте статус:**
   ```bash
   sudo wg show
   ```

2. **Проверьте порты:**
   ```bash
   sudo netstat -ulnp | grep 51820
   ```

3. **Перезапустите:**
   ```bash
   sudo wg-quick down wg0
   sudo wg-quick up wg0
   ```

---

## 📚 Подробные инструкции

- **Полная инструкция по WireGuard:** `WIREGUARD_SETUP.md`
- **Чек-лист настройки:** `SERVER_SETUP_CHECKLIST.md`
- **Документация по развертыванию:** `DEPLOY.md`

---

## 🎯 Что делает бот

1. ✅ Принимает заказы через Telegram
2. ✅ Автоматически проверяет платежи через API ЮMoney
3. ✅ Генерирует конфиги WireGuard для клиентов
4. ✅ Автоматически добавляет клиентов на WireGuard сервер
5. ✅ Отправляет конфиги клиентам для установки

**Клиенты просто устанавливают приложение WireGuard, вставляют конфиг - и VPN работает!** 🔐

---

**Успешной настройки!** 🚀

