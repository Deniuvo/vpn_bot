# ⚡ Быстрое исправление VPN

## 🚨 Если VPN не работает - выполните это:

### Шаг 1: Запустите диагностику

```bash
cd /root/vpn_bot
chmod +x fix_vpn.sh
./fix_vpn.sh
```

Скрипт автоматически:
- ✅ Проверит WireGuard
- ✅ Проверит IP forwarding
- ✅ Проверит iptables правила
- ✅ Исправит проблемы, если возможно
- ✅ Покажет, что не так

---

## 🔧 Основные проблемы и решения:

### ❌ Проблема 1: Нет peers на сервере (0 peers)

**Симптомы:** `wg show wg0` показывает 0 peers

**Решение:**
```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 find_and_add_peer.py
# Выберите опцию 1 - добавить всех пользователей
```

---

### ❌ Проблема 2: IP forwarding отключен

**Симптомы:** VPN подключен, но интернет не работает

**Решение:**
```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

---

### ❌ Проблема 3: Нет правил iptables

**Симптомы:** Трафик не проходит через VPN

**Решение:**
```bash
# Найдите основной интерфейс
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)

# Добавьте правила
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE
```

---

### ❌ Проблема 4: WireGuard не запущен

**Симптомы:** `ip link show wg0` показывает DOWN

**Решение:**
```bash
wg-quick up wg0
systemctl enable wg-quick@wg0
systemctl status wg-quick@wg0
```

---

## 🎯 Полное исправление одной командой:

```bash
cd /root/vpn_bot && \
chmod +x fix_vpn.sh && \
./fix_vpn.sh && \
cd /root/vpn_bot && \
source vpn_env/bin/activate && \
python3 find_and_add_peer.py
```

---

## 📋 Пошаговая диагностика:

### 1. Проверьте статус WireGuard:
```bash
wg show wg0
```
**Ожидается:** Должны быть секции `[Peer]` с вашими peers

### 2. Проверьте количество peers:
```bash
wg show wg0 peers | wc -l
```
**Ожидается:** Больше 0

### 3. Проверьте IP forwarding:
```bash
cat /proc/sys/net/ipv4/ip_forward
```
**Ожидается:** `1`

### 4. Проверьте iptables:
```bash
iptables -t nat -L POSTROUTING -n -v | grep MASQUERADE
```
**Ожидается:** Есть правило MASQUERADE

### 5. Проверьте на клиенте:
- Подключите VPN
- Откройте https://ifconfig.me
- **Ожидается:** IP вашего сервера, а не ваш локальный IP

---

## 🆘 Если ничего не помогает:

1. **Полный перезапуск:**
```bash
wg-quick down wg0
wg-quick up wg0
systemctl restart wg-quick@wg0
```

2. **Проверьте логи:**
```bash
journalctl -u wg-quick@wg0 -n 100
tail -n 100 /root/vpn_bot/vpn.log
```

3. **Проверьте конфигурацию:**
```bash
cat /etc/wireguard/wg0.conf
```

4. **Свяжитесь с поддержкой через бота:**
```
/support
```

---

## 💡 Профилактика:

1. **Регулярно проверяйте peers:**
```bash
wg show wg0
```

2. **Сохраняйте peers в конфиг:**
После добавления через `wg set`, добавляйте в `/etc/wireguard/wg0.conf`

3. **Мониторинг:**
```bash
watch -n 5 'wg show wg0'
```

