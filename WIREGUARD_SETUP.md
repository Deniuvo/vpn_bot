# 🔐 Полная инструкция по установке и настройке WireGuard на сервере

Эта инструкция поможет вам установить и настроить WireGuard сервер для работы с VPN ботом.

---

## ⚠️ ВАЖНО: Защита SSH соединения

**При неправильной настройке WireGuard может закрыться доступ к серверу через SSH/консоль!**

✅ **Хорошие новости:** Эта инструкция включает **автоматическую защиту SSH** через специальные правила iptables.

**Что делают правила защиты:**
- SSH трафик всегда идет через основной сетевой интерфейс (НЕ через WireGuard)
- Это гарантирует, что доступ к серверу сохранится даже при запуске WireGuard
- Правила автоматически добавляются в конфигурацию при использовании скрипта `setup_wireguard.sh`

**Если настраиваете вручную:** Обязательно добавьте правила защиты SSH в PostUp/PostDown (см. раздел 4).

---

## 📋 Содержание

1. [Установка WireGuard](#1-установка-wireguard)
2. [Генерация ключей сервера](#2-генерация-ключей-сервера)
3. [Определение сетевого интерфейса](#3-определение-сетевого-интерфейса)
4. [Создание конфигурации сервера](#4-создание-конфигурации-сервера)
5. [Включение IP Forwarding](#5-включение-ip-forwarding)
6. [Открытие портов в файрволе](#6-открытие-портов-в-файрволе)
7. [Запуск WireGuard](#7-запуск-wireguard)
8. [Автозапуск при перезагрузке](#8-автозапуск-при-перезагрузке)
9. [Проверка работы](#9-проверка-работы)
10. [Настройка переменных для бота](#10-настройка-переменных-для-бота)

---

## 1. Установка WireGuard

```bash
# Обновление списка пакетов
sudo apt update

# Установка WireGuard и инструментов
sudo apt install wireguard wireguard-tools -y

# Проверка установки
wg --version
```

**Результат:** Должна отобразиться версия WireGuard.

---

## 2. Генерация ключей сервера

```bash
# Переходим в директорию WireGuard
cd /etc/wireguard

# Генерируем приватный ключ сервера
sudo wg genkey | sudo tee private.key

# Устанавливаем правильные права доступа (только root может читать)
sudo chmod 600 private.key

# Генерируем публичный ключ из приватного
sudo cat private.key | sudo wg pubkey | sudo tee public.key

# Просматриваем ключи
echo "=== ПРИВАТНЫЙ КЛЮЧ СЕРВЕРА (НЕ ПОКАЗЫВАЙТЕ НИКОМУ!) ==="
sudo cat private.key
echo ""
echo "=== ПУБЛИЧНЫЙ КЛЮЧ СЕРВЕРА (нужен для бота) ==="
sudo cat public.key
```

**⚠️ ВАЖНО:** 
- Сохраните публичный ключ - он понадобится для настройки бота
- Приватный ключ должен оставаться секретным

---

## 3. Определение сетевого интерфейса

Нужно узнать имя вашего основного сетевого интерфейса (обычно `eth0`, `ens3`, `enp0s3` и т.д.):

```bash
# Просмотр всех сетевых интерфейсов
ip addr show

# Или альтернативный способ
ifconfig

# Или еще один способ
ls /sys/class/net/
```

**Найдите интерфейс с вашим публичным IP адресом.** Обычно это не `lo` (loopback). Запишите имя (например: `eth0`, `ens3`, `enp0s3`).

---

## 4. Создание конфигурации сервера

```bash
# Создаем конфигурационный файл
sudo nano /etc/wireguard/wg0.conf
```

**Вставьте следующую конфигурацию** (замените значения):

```ini
[Interface]
# Вставьте сюда приватный ключ сервера (из /etc/wireguard/private.key)
PrivateKey = ВСТАВЬТЕ_ПРИВАТНЫЙ_КЛЮЧ_СЮДА

# IP адрес интерфейса WireGuard на сервере
Address = 10.0.0.1/24

# Порт для прослушивания (по умолчанию 51820)
ListenPort = 51820

# Команды, выполняемые при запуске интерфейса
# ВАЖНО: Замените eth0 на имя вашего сетевого интерфейса!
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Команды, выполняемые при остановке интерфейса
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```

**Где:**
- `PrivateKey` - ваш приватный ключ из `/etc/wireguard/private.key`
- `Address = 10.0.0.1/24` - IP адрес сервера в сети WireGuard
- `ListenPort = 51820` - порт для WireGuard
- `eth0` в PostUp/PostDown - замените на имя вашего сетевого интерфейса!

**Пример полного конфига с защитой SSH:**

```ini
[Interface]
PrivateKey = 8JZvJ7xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=
Address = 10.0.0.1/24
ListenPort = 51820
# ⚠️ ВАЖНО: Правила защиты SSH - SSH трафик НЕ будет идти через WireGuard!
# Это предотвратит закрытие доступа к серверу через SSH/консоль
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; iptables -t nat -A POSTROUTING -o eth0 -p tcp --dport 22 -j ACCEPT; iptables -A OUTPUT -o eth0 -p tcp --sport 22 -j ACCEPT; iptables -A OUTPUT -o eth0 -p tcp --dport 22 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE; iptables -t nat -D POSTROUTING -o eth0 -p tcp --dport 22 -j ACCEPT; iptables -D OUTPUT -o eth0 -p tcp --sport 22 -j ACCEPT; iptables -D OUTPUT -o eth0 -p tcp --dport 22 -j ACCEPT
```

**⚠️ ЗАЩИТА SSH:**
- Если ваш SSH использует нестандартный порт (не 22), замените `--dport 22` на ваш порт
- Эти правила гарантируют, что SSH трафик всегда идет через основной интерфейс (`eth0`)
- Это предотвратит закрытие доступа к серверу при запуске WireGuard

**Сохранение:**
- В nano: `Ctrl+O`, затем `Enter`, затем `Ctrl+X`

**Устанавливаем правильные права доступа:**

```bash
sudo chmod 600 /etc/wireguard/wg0.conf
```

---

## 5. Включение IP Forwarding

Это необходимо для маршрутизации трафика между интерфейсами:

```bash
# Включаем IP forwarding временно (до перезагрузки)
sudo sysctl -w net.ipv4.ip_forward=1

# Включаем IP forwarding постоянно (после перезагрузки)
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Применяем изменения
sudo sysctl -p
```

**Проверка:**

```bash
cat /proc/sys/net/ipv4/ip_forward
```

**Должно быть:** `1`

---

## 6. Открытие портов в файрволе

### Для UFW (Ubuntu Firewall):

```bash
# Разрешаем UDP порт 51820 для WireGuard
sudo ufw allow 51820/udp

# Разрешаем TCP порт 5000 для HTTP сервера конфигов (для бота)
sudo ufw allow 5000/tcp

# Если UFW включен, проверяем статус
sudo ufw status
```

### Для iptables (если UFW не используется):

```bash
# Разрешаем UDP порт 51820 для WireGuard
sudo iptables -A INPUT -p udp --dport 51820 -j ACCEPT

# Разрешаем TCP порт 5000 для HTTP сервера конфигов
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# Сохраняем правила iptables (Ubuntu/Debian)
sudo netfilter-persistent save
```

**Или если используете firewalld (CentOS/RHEL):**

```bash
sudo firewall-cmd --permanent --add-port=51820/udp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

---

## 7. Запуск WireGuard

```bash
# Запуск интерфейса wg0
sudo wg-quick up wg0

# Проверка статуса
sudo wg show
```

**Ожидаемый результат:**

```
interface: wg0
  public key: ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ
  private key: (hidden)
  listening port: 51820
```

**Если видите ошибки:**
- Проверьте права доступа к файлу `/etc/wireguard/wg0.conf` (должен быть 600)
- Убедитесь, что порт 51820 не занят: `sudo netstat -ulnp | grep 51820`
- Проверьте логи: `sudo journalctl -u wg-quick@wg0 -n 50`

---

## 8. Автозапуск при перезагрузке

```bash
# Включаем автозапуск WireGuard
sudo systemctl enable wg-quick@wg0

# Проверяем статус
sudo systemctl status wg-quick@wg0
```

**Проверка автозапуска:**

```bash
# Перезагружаем сервер (опционально, для проверки)
# sudo reboot

# После перезагрузки проверяем
sudo wg show
```

---

## 9. Проверка работы

```bash
# Проверка интерфейса WireGuard
sudo wg show wg0

# Проверка IP адреса интерфейса
ip addr show wg0

# Должно быть: 10.0.0.1/24

# Проверка маршрутизации
ip route show

# Проверка работы iptables
sudo iptables -t nat -L POSTROUTING -v
```

**Все должно работать, если вы видите:**
- Интерфейс `wg0` активен
- IP адрес `10.0.0.1/24` назначен
- Порт 51820 прослушивается

---

## 10. Настройка переменных для бота

Теперь нужно получить данные для настройки бота:

### Автоматический способ:

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 setup_server.py
```

Этот скрипт покажет вам:
- Публичный IP сервера
- Публичный ключ WireGuard

### Ручной способ:

```bash
# Получаем публичный IP сервера
curl ifconfig.me
# или
curl ipinfo.io/ip

# Получаем публичный ключ WireGuard
sudo cat /etc/wireguard/public.key
# или
sudo wg show wg0 public-key
```

### Устанавливаем переменные окружения:

```bash
# Получаем данные (замените на свои!)
export SERVER_IP="ВАН_ПУБЛИЧНЫЙ_IP"
export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ_WIREGUARD"
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="true"
```

### Для постоянного сохранения:

```bash
# Добавляем в ~/.bashrc
echo 'export SERVER_IP="ВАШ_ПУБЛИЧНЫЙ_IP"' >> ~/.bashrc
echo 'export SERVER_PUBLIC_KEY="ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ"' >> ~/.bashrc
echo 'export YMONEY_ACCESS_TOKEN="ваш_токен"' >> ~/.bashrc
echo 'export USE_YOOMONEY_API="true"' >> ~/.bashrc

# Применяем изменения
source ~/.bashrc
```

---

## ✅ Финальная проверка перед запуском бота

Выполните все проверки:

```bash
# 1. WireGuard запущен
sudo wg show

# 2. IP forwarding включен
cat /proc/sys/net/ipv4/ip_forward  # Должно быть 1

# 3. Порт открыт
sudo netstat -ulnp | grep 51820

# 4. Переменные окружения установлены
echo $SERVER_IP
echo $SERVER_PUBLIC_KEY

# 5. Все готово к запуску бота!
cd /root/vpn_bot
source vpn_env/bin/activate
python3 main.py
```

---

## 🎯 Как работает интеграция с ботом

1. **Клиент покупает подписку** через Telegram бота
2. **Бот генерирует ключи** для клиента
3. **Бот создает конфиг** WireGuard для клиента
4. **Бот добавляет peer на сервер** командой: `wg set wg0 peer <public_key> allowed-ips <ip>/32`
5. **Бот отправляет конфиг** клиенту через Telegram
6. **Клиент подключается** используя конфиг в приложении WireGuard
7. **VPN работает!** Трафик маршрутизируется через ваш сервер

---

## 🔧 Полезные команды для управления

```bash
# Просмотр всех подключенных клиентов
sudo wg show

# Добавление клиента вручную (обычно делает бот)
sudo wg set wg0 peer ПУБЛИЧНЫЙ_КЛЮЧ_КЛИЕНТА allowed-ips 10.0.0.5/32

# Удаление клиента
sudo wg set wg0 peer ПУБЛИЧНЫЙ_КЛЮЧ_КЛИЕНТА remove

# Перезапуск WireGuard
sudo wg-quick down wg0
sudo wg-quick up wg0

# Просмотр логов
sudo journalctl -u wg-quick@wg0 -f
```

---

## ⚠️ Решение проблем

### Потеря доступа к серверу через SSH после запуска WireGuard

**Если вы потеряли доступ к серверу через SSH:**

1. **Через консоль провайдера/хостинга:**
   - Используйте консоль управления сервером от провайдера
   - Отключите WireGuard: `sudo wg-quick down wg0`
   - Проверьте SSH: `sudo systemctl status ssh`

2. **Исправление конфигурации:**
   - Добавьте правила защиты SSH в `/etc/wireguard/wg0.conf`
   - Перезапустите WireGuard: `sudo wg-quick down wg0 && sudo wg-quick up wg0`

3. **Проверка правил защиты SSH:**
   ```bash
   sudo iptables -L OUTPUT -n | grep 22
   sudo iptables -t nat -L POSTROUTING -n | grep 22
   ```
   Должны быть правила для порта 22 (SSH).

4. **Если SSH на нестандартном порту:**
   - Найдите ваш SSH порт: `grep "^Port" /etc/ssh/sshd_config`
   - Замените `--dport 22` на ваш порт в конфиге WireGuard

### WireGuard не запускается

```bash
# Проверьте конфигурацию
sudo wg-quick up wg0

# Проверьте логи
sudo journalctl -u wg-quick@wg0 -n 50

# Проверьте права доступа
ls -la /etc/wireguard/wg0.conf  # Должно быть -rw------- (600)
```

### Клиенты не могут подключиться

1. **Проверьте порт:** `sudo netstat -ulnp | grep 51820`
2. **Проверьте файрвол:** `sudo ufw status` или `sudo iptables -L`
3. **Проверьте IP forwarding:** `cat /proc/sys/net/ipv4/ip_forward` (должно быть 1)
4. **Проверьте публичный IP:** убедитесь, что в конфиге клиента указан правильный IP

### Не работает интернет у клиентов

1. **Проверьте NAT (MASQUERADE):**
   ```bash
   sudo iptables -t nat -L POSTROUTING -v
   ```
   Должна быть строка с MASQUERADE для вашего интерфейса

2. **Проверьте PostUp команды** в `/etc/wireguard/wg0.conf`

---

## 📝 Быстрая шпаргалка команд

```bash
# Установка
sudo apt update && sudo apt install wireguard wireguard-tools -y

# Генерация ключей
sudo wg genkey | sudo tee /etc/wireguard/private.key
sudo chmod 600 /etc/wireguard/private.key
sudo cat /etc/wireguard/private.key | sudo wg pubkey | sudo tee /etc/wireguard/public.key

# IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Файрвол
sudo ufw allow 51820/udp
sudo ufw allow 5000/tcp

# Запуск
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0

# Проверка
sudo wg show
```

---

**Готово! WireGuard настроен и готов к работе с ботом! 🚀**

