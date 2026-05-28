# ⚡ Простое исправление Shadowsocks

## 🔍 Проблема

`ss-server` работает, но systemd не может его запустить из-за неправильного формата override конфига.

---

## ✅ Быстрое решение

```bash
cd /root/vpn_bot
chmod +x fix_systemd_override.sh
sudo bash fix_systemd_override.sh
```

---

## 📋 Или вручную (3 команды):

```bash
# 1. Остановить сервис
sudo systemctl stop shadowsocks-libev

# 2. Создать override с ПРАВИЛЬНЫМ форматом (с кавычками вокруг пути!)
sudo mkdir -p /etc/systemd/system/shadowsocks-libev.service.d/
sudo bash -c 'cat > /etc/systemd/system/shadowsocks-libev.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=/usr/bin/ss-server -c "/etc/shadowsocks-libev/config.json" -u
EOF'

# 3. Перезапустить
sudo systemctl daemon-reload
sudo systemctl restart shadowsocks-libev
sudo systemctl status shadowsocks-libev
```

---

## 🔧 Ключевое отличие

**Неправильно (без кавычек):**
```
ExecStart=/usr/bin/ss-server -c /etc/shadowsocks-libev/config.json -u
```

**Правильно (с кавычками):**
```
ExecStart=/usr/bin/ss-server -c "/etc/shadowsocks-libev/config.json" -u
```

Кавычки важны, чтобы systemd правильно передал путь к конфигу!

---

## ✅ Проверка

```bash
# Статус
sudo systemctl status shadowsocks-libev

# Логи
sudo journalctl -u shadowsocks-libev -f

# Проверка порта
sudo netstat -tulnp | grep 8388
```

---

Запустите скрипт и сообщите результат! 🚀

