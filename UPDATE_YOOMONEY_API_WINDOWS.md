# Обновление yoomoney_api.py на сервере (Windows)

## 🚀 Быстрый способ - одна команда

Откройте PowerShell или CMD в папке проекта и выполните:

```powershell
scp yoomoney_api.py root@90.156.169.27:/root/vpn_bot/
```

**Или используйте PowerShell скрипт:**

```powershell
.\update_yoomoney_api.ps1 root@90.156.169.27
```

---

## 📋 Пошаговая инструкция

### Вариант 1: Через PowerShell (если установлен OpenSSH)

1. Откройте PowerShell
2. Перейдите в папку проекта:
   ```powershell
   cd C:\Users\1\Desktop\vpn_bot
   ```
3. Выполните команду:
   ```powershell
   scp yoomoney_api.py root@90.156.169.27:/root/vpn_bot/
   ```
4. Введите пароль от сервера (если потребуется)

### Вариант 2: Через WinSCP (рекомендуется для Windows)

1. Скачайте WinSCP: https://winscp.net/
2. Подключитесь к серверу:
   - Host: `90.156.169.27`
   - User: `root`
   - Password: ваш пароль
3. Перейдите в папку `/root/vpn_bot/`
4. Перетащите файл `yoomoney_api.py` из вашего компьютера в эту папку
5. Замените существующий файл

### Вариант 3: Через PuTTY pscp

1. Скачайте PuTTY: https://www.putty.org/
2. Откройте командную строку (CMD)
3. Перейдите в папку PuTTY (обычно `C:\Program Files\PuTTY`)
4. Выполните:
   ```cmd
   pscp C:\Users\1\Desktop\vpn_bot\yoomoney_api.py root@90.156.169.27:/root/vpn_bot/
   ```

---

## 🔄 После копирования - перезапуск бота

После успешного копирования файла подключитесь к серверу и перезапустите бота:

### Через SSH:

```bash
ssh root@90.156.169.27
cd /root/vpn_bot
pkill -f "python3 main.py"
bash start_bot.sh
```

### Или одной командой:

```powershell
ssh root@90.156.169.27 "cd /root/vpn_bot && pkill -f 'python3 main.py' && bash start_bot.sh"
```

---

## ✅ Проверка

После перезапуска проверьте логи бота:

```bash
ssh root@90.156.169.27
tail -f /root/vpn_bot/vpn.log
```

---

## 🆘 Если команда scp не работает

**Установите OpenSSH для Windows:**

1. Откройте "Параметры Windows" → "Приложения"
2. Нажмите "Дополнительные компоненты"
3. Найдите "OpenSSH клиент" и установите

Или используйте WinSCP (рекомендуется для Windows).

