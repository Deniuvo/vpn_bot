# ✅ Проверка файлов на сервере

## 🔍 Проверка наличия файлов

Подключитесь к серверу и проверьте:

```bash
ssh root@ваш_сервер
cd /root/vpn_bot
ls -la
```

## 📋 Необходимые файлы

Должны присутствовать следующие файлы:

### Обязательные для работы:
- ✅ `setup_wireguard.sh` - **ВАЖНО!** Скрипт установки WireGuard
- ✅ `bot.py` - главный файл бота
- ✅ `main.py` - точка входа
- ✅ `database.py` - база данных
- ✅ `wireguard.py` - управление WireGuard
- ✅ `config_server.py` - HTTP сервер
- ✅ `yoomoney_api.py` - API ЮMoney
- ✅ `requirements.txt` - зависимости

### Дополнительные:
- ✅ `setup.sh` - установка зависимостей
- ✅ `setup_server.py` - определение IP и ключей
- ✅ `wireguard_server_example.conf` - пример конфига

## ❌ Если файлов нет

### Вариант 1: Скопировать через скрипт (с вашего компьютера)

```bash
# Linux/Mac
chmod +x quick_copy.sh
./quick_copy.sh root@ваш_сервер

# Или полный скрипт
chmod +x copy_to_server.sh
./copy_to_server.sh root@ваш_сервер
```

### Вариант 2: Ручное копирование через SCP

```bash
# С вашего компьютера
cd ~/Desktop/vpn_bot
scp setup_wireguard.sh root@ваш_сервер:/root/vpn_bot/
scp bot.py main.py database.py wireguard.py config_server.py root@ваш_сервер:/root/vpn_bot/
scp yoomoney_api.py yoomoney_oauth.py setup_server.py root@ваш_сервер:/root/vpn_bot/
scp requirements.txt root@ваш_сервер:/root/vpn_bot/
```

### Вариант 3: WinSCP (Windows)

1. Откройте WinSCP
2. Подключитесь к серверу
3. Перетащите папку `vpn_bot` в `/root/`

### Вариант 4: Скопировать только setup_wireguard.sh

Если нужно только установить WireGuard:

```bash
# С вашего компьютера
scp setup_wireguard.sh root@ваш_сервер:/root/vpn_bot/
```

Затем на сервере:
```bash
cd /root/vpn_bot
sudo bash setup_wireguard.sh
```

## ✅ Проверка после копирования

```bash
# На сервере
cd /root/vpn_bot
ls -la setup_wireguard.sh  # Должен быть виден
ls -la bot.py               # Должен быть виден
ls -la requirements.txt     # Должен быть виден
```

Если файлы есть, можно продолжать установку!

## 🔧 Быстрое решение

Если вы уже на сервере и файлов нет:

1. **Выйдите с сервера:**
   ```bash
   exit
   ```

2. **Скопируйте файлы с вашего компьютера:**
   ```bash
   cd ~/Desktop/vpn_bot
   scp -r . root@ваш_сервер:/root/vpn_bot
   ```

3. **Вернитесь на сервер:**
   ```bash
   ssh root@ваш_сервер
   cd /root/vpn_bot
   ```

4. **Проверьте:**
   ```bash
   ls -la setup_wireguard.sh
   ```

---

**После копирования файлов установка будет работать! 🚀**

