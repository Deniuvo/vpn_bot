# 🔒 Защита SSH соединения при использовании WireGuard

## ⚠️ Проблема

При неправильной настройке WireGuard **может закрыться доступ к серверу через SSH/консоль**. Это происходит, если весь трафик (включая SSH) начинает маршрутизироваться через WireGuard.

## ✅ Решение

**Автоматическая защита включена** во всех скриптах и инструкциях этого проекта. SSH трафик будет автоматически исключен из маршрутизации через WireGuard.

---

## 🔧 Как работает защита

Специальные правила iptables гарантируют, что:
1. SSH трафик всегда идет через основной сетевой интерфейс
2. SSH трафик НЕ маршрутизируется через WireGuard
3. Доступ к серверу сохраняется даже при запуске WireGuard

---

## 📝 Правила защиты SSH в конфигурации

В конфигурации `/etc/wireguard/wg0.conf` должны быть такие правила в `PostUp` и `PostDown`:

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820

# Защита SSH (порт 22 по умолчанию)
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; \
         iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; \
         iptables -t nat -A POSTROUTING -o eth0 -p tcp --dport 22 -j ACCEPT; \
         iptables -A OUTPUT -o eth0 -p tcp --sport 22 -j ACCEPT; \
         iptables -A OUTPUT -o eth0 -p tcp --dport 22 -j ACCEPT

PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; \
           iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE; \
           iptables -t nat -D POSTROUTING -o eth0 -p tcp --dport 22 -j ACCEPT; \
           iptables -D OUTPUT -o eth0 -p tcp --sport 22 -j ACCEPT; \
           iptables -D OUTPUT -o eth0 -p tcp --dport 22 -j ACCEPT
```

**Замените:**
- `eth0` на имя вашего сетевого интерфейса
- `22` на ваш SSH порт, если используете нестандартный

---

## 🚀 Автоматическая установка с защитой

**Рекомендуется использовать скрипт автоматической установки:**

```bash
sudo bash setup_wireguard.sh
```

Скрипт автоматически:
- ✅ Определит ваш SSH порт
- ✅ Определит ваш сетевой интерфейс
- ✅ Добавит правила защиты SSH
- ✅ Настроит всё правильно

---

## 🔍 Проверка защиты SSH

### Проверка правил iptables

```bash
# Проверка OUTPUT правил для SSH
sudo iptables -L OUTPUT -n -v | grep 22

# Проверка NAT правил для SSH
sudo iptables -t nat -L POSTROUTING -n -v | grep 22
```

Должны быть правила, разрешающие SSH трафик через основной интерфейс.

### Проверка маршрутизации SSH

```bash
# Проверка маршрута для SSH соединения
ip route get $(who am i | awk '{print $5}')

# Проверка, что SSH идет через правильный интерфейс
ss -tnp | grep :22
```

SSH должен идти через основной интерфейс (не wg0).

---

## 🛠️ Если SSH на нестандартном порту

Если ваш SSH использует нестандартный порт (не 22):

### 1. Узнайте ваш SSH порт:

```bash
grep "^Port" /etc/ssh/sshd_config
# или
sudo netstat -tlnp | grep sshd
```

### 2. Обновите конфигурацию WireGuard:

В `/etc/wireguard/wg0.conf` замените `--dport 22` на ваш порт:

```bash
sudo nano /etc/wireguard/wg0.conf
```

Найдите строки с `--dport 22` и замените на ваш порт.

### 3. Перезапустите WireGuard:

```bash
sudo wg-quick down wg0
sudo wg-quick up wg0
```

---

## 🆘 Что делать, если потеряли доступ к SSH

### Способ 1: Консоль провайдера

1. Войдите через консоль управления сервером от вашего провайдера
2. Отключите WireGuard:
   ```bash
   sudo wg-quick down wg0
   ```
3. Исправьте конфигурацию и добавьте правила защиты SSH
4. Перезапустите WireGuard

### Способ 2: VNC/IPMI консоль

Если доступна VNC/IPMI консоль:
1. Подключитесь через консоль
2. Отключите WireGuard: `sudo wg-quick down wg0`
3. Исправьте конфигурацию

### Способ 3: Через другой SSH сессию

Если у вас открыта еще одна SSH сессия:
1. НЕ закрывайте текущую сессию
2. В другой сессии отключите WireGuard: `sudo wg-quick down wg0`
3. Исправьте конфигурацию
4. Перезапустите WireGuard

---

## ✅ Проверка после настройки

После настройки WireGuard с защитой SSH:

1. **Запустите WireGuard:**
   ```bash
   sudo wg-quick up wg0
   ```

2. **Проверьте SSH доступ:**
   - Попробуйте подключиться к серверу через SSH
   - Доступ должен работать нормально

3. **Проверьте правила:**
   ```bash
   sudo iptables -L OUTPUT -n | grep 22
   ```

4. **Проверьте маршрутизацию:**
   ```bash
   sudo ip route show
   ```
   SSH трафик должен идти через основной интерфейс, а не wg0.

---

## 📚 Дополнительная информация

- **Подробная инструкция:** `WIREGUARD_SETUP.md`
- **Автоматическая установка:** `setup_wireguard.sh`
- **Пример конфигурации:** `wireguard_server_example.conf`

---

**С защитой SSH, настроенной правильно, ваш доступ к серверу будет в безопасности!** 🔒✅

