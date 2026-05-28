# 🔧 Решение проблем с VPN подключением

Если VPN подключен, но не работает (не открываются запрещенные сайты), выполните эти шаги:

## 🔍 Быстрая диагностика на сервере

Запустите скрипт диагностики:

```bash
cd /root/vpn_bot
chmod +x check_vpn_server.sh
./check_vpn_server.sh
```

Скрипт проверит:
- ✅ Установлен ли WireGuard
- ✅ Запущен ли интерфейс wg0
- ✅ Включен ли IP forwarding
- ✅ Настроены ли iptables правила
- ✅ Открыт ли порт 51820 в файрволе
- ✅ Работает ли сервис WireGuard

## 🔧 Частые проблемы и решения

### ❌ Проблема 1: IP Forwarding отключен

**Симптомы:** VPN подключен, но трафик не проходит через сервер.

**Решение:**
```bash
# Включить IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Проверка
cat /proc/sys/net/ipv4/ip_forward
# Должно быть: 1
```

### ❌ Проблема 2: Неправильные правила iptables

**Симптомы:** Подключение есть, но интернет не работает.

**Решение:**

1. Найдите основной сетевой интерфейс:
```bash
ip route | grep default
# Запомните интерфейс (обычно eth0, ens3, ens33 и т.д.)
```

2. Добавьте правила iptables:
```bash
INTERFACE="eth0"  # Замените на ваш интерфейс!

# FORWARD правило
iptables -A FORWARD -i wg0 -j ACCEPT

# NAT MASQUERADE
iptables -t nat -A POSTROUTING -o $INTERFACE -j MASQUERADE
```

3. Сохраните правила (Ubuntu/Debian):
```bash
apt install iptables-persistent -y
iptables-save > /etc/iptables/rules.v4
```

4. **Важно:** Обновите `/etc/wireguard/wg0.conf`:
```ini
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```

Замените `eth0` на ваш интерфейс!

### ❌ Проблема 3: Неправильный сетевой интерфейс в конфиге

**Симптомы:** VPN работает, но периодически обрывается или не работает интернет.

**Решение:**

1. Найдите правильный интерфейс:
```bash
ip addr show
# Ищите интерфейс с вашим публичным IP (обычно eth0, ens3, ens33)
```

2. Проверьте, что в `/etc/wireguard/wg0.conf` указан правильный интерфейс в PostUp/PostDown.

3. Перезапустите WireGuard:
```bash
wg-quick down wg0
wg-quick up wg0
```

### ❌ Проблема 4: Файрвол блокирует трафик

**Решение для UFW:**
```bash
ufw allow 51820/udp
ufw allow 5000/tcp  # Для HTTP сервера конфигов
ufw reload
```

**Решение для iptables:**
```bash
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### ❌ Проблема 5: Peer не добавлен на сервер

**Симптомы:** Клиент не может подключиться к серверу.

**Проверка:**
```bash
wg show wg0
```

Должен быть список peers с их публичными ключами.

**Если peers нет:**
1. Проверьте, что бот правильно добавил peer
2. Добавьте вручную:
```bash
wg set wg0 peer <PUBLIC_KEY> allowed-ips <IP_ADDRESS>/32
```

### ❌ Проблема 6: DNS не работает

**Симптомы:** Сайты не открываются по имени, но работают по IP.

**Решение:**
1. Проверьте DNS в конфиге клиента - должен быть `DNS = 8.8.8.8`
2. Если проблема сохраняется, попробуйте другие DNS:
   - `1.1.1.1` (Cloudflare)
   - `8.8.4.4` (Google альтернативный)

## 📋 Полная диагностика

### 1. Проверка WireGuard сервера

```bash
# Статус интерфейса
ip link show wg0

# Статус WireGuard
wg show wg0

# Статус сервиса
systemctl status wg-quick@wg0

# Логи
journalctl -u wg-quick@wg0 -n 50
```

### 2. Проверка маршрутизации

```bash
# Проверка IP forwarding
sysctl net.ipv4.ip_forward

# Проверка маршрутов
ip route show
ip route show table all | grep wg0
```

### 3. Проверка iptables

```bash
# FORWARD правила
iptables -L FORWARD -n -v

# NAT правила
iptables -t nat -L POSTROUTING -n -v

# INPUT правила (порт 51820)
iptables -L INPUT -n -v | grep 51820
```

### 4. Проверка подключения клиента

**На клиенте (мобильное устройство/компьютер):**

1. Проверьте, что VPN подключен
2. Откройте сайт для проверки IP: https://ifconfig.me
3. IP должен быть IP вашего сервера

**Если IP не изменился:**
- Проверьте, что `AllowedIPs = 0.0.0.0/0` в конфиге клиента
- Переподключите VPN
- Перезапустите приложение WireGuard

### 5. Проверка трафика

На сервере:
```bash
# Смотрим статистику передачи данных
wg show wg0 transfer

# Мониторим в реальном времени
watch -n 1 'wg show wg0 transfer'
```

Если `transfer` показывает 0 для вашего peer - трафик не проходит.

## 🔄 Быстрое исправление всех проблем

Если ничего не помогает, выполните полную перенастройку:

```bash
cd /root/vpn_bot

# 1. Остановите WireGuard
wg-quick down wg0

# 2. Найдите основной интерфейс
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)
echo "Основной интерфейс: $MAIN_INTERFACE"

# 3. Обновите конфигурацию
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat /etc/wireguard/private.key)
Address = 10.0.0.1/24
ListenPort = 51820

PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE
EOF

# 4. Включите IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# 5. Откройте порты в файрволе
ufw allow 51820/udp || iptables -A INPUT -p udp --dport 51820 -j ACCEPT

# 6. Запустите WireGuard
wg-quick up wg0
systemctl enable wg-quick@wg0
```

## 📞 Если проблема сохраняется

1. Проверьте логи WireGuard: `journalctl -u wg-quick@wg0 -f`
2. Проверьте логи бота: `tail -f /root/vpn_bot/vpn.log`
3. Запустите диагностику: `./check_vpn_server.sh`
4. Свяжитесь с поддержкой через бота: `/support`

