# 🔒 Автоматическое отключение VPN при истечении подписки

## ✅ Гарантия: После истечения срока VPN **полностью перестает работать**!

Теперь система **автоматически удаляет peer с WireGuard сервера**, поэтому VPN перестает работать даже если конфиг установлен на устройстве.

---

## 🛠️ Как это работает:

### 1. **При запросе конфига (/myconfig):**
- Бот проверяет срок подписки
- Если подписка истекла → **автоматически удаляет peer с сервера**
- VPN сразу перестает работать

### 2. **Периодическая проверка (скрипт):**
- Скрипт `remove_expired_peers.py` находит всех пользователей с истекшей подпиской
- Удаляет их peers с WireGuard сервера
- Деактивирует в базе данных

### 3. **Что происходит при удалении:**
- ✅ Peer удаляется из работающего WireGuard интерфейса
- ✅ Peer удаляется из конфига `/etc/wireguard/wg0.conf`
- ✅ Пользователь деактивируется в базе данных
- ✅ VPN перестает работать **немедленно**

---

## 📋 Установка и настройка:

### Вариант 1: Автоматическая проверка через cron (рекомендуется)

**Используйте скрипт-обертку `remove_expired_peers.sh`:**

```bash
# 1. Сделайте скрипт исполняемым
chmod +x /root/vpn_bot/remove_expired_peers.sh

# 2. Редактируем crontab
crontab -e

# 3. Добавляем строку (проверка каждый день в 3:00 утра)
0 3 * * * /root/vpn_bot/remove_expired_peers.sh >> /root/vpn_bot/expired_peers.log 2>&1
```

### Вариант 2: Ручной запуск через скрипт (рекомендуется)

```bash
cd /root/vpn_bot
chmod +x remove_expired_peers.sh
./remove_expired_peers.sh
```

Или напрямую через Python (если переменные окружения установлены):

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
export SERVER_IP="your_server_ip"
export SERVER_PUBLIC_KEY="your_public_key"
python3 remove_expired_peers.py
```

### Вариант 3: Через несколько запусков в день

Если хотите проверять чаще (например, каждые 6 часов):

```bash
0 */6 * * * cd /root/vpn_bot && source vpn_env/bin/activate && python3 remove_expired_peers.py >> /root/vpn_bot/expired_peers.log 2>&1
```

---

## 🔍 Проверка работы:

### 1. Проверьте, что скрипт работает:

```bash
cd /root/vpn_bot
chmod +x remove_expired_peers.sh
./remove_expired_peers.sh
```

Или напрямую через Python:

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
export SERVER_IP="your_server_ip"
export SERVER_PUBLIC_KEY="your_public_key"
python3 remove_expired_peers.py
```

Вывод должен показать:
- Сколько пользователей с истекшей подпиской найдено
- Какие peers были удалены
- Итоговую статистику

### 2. Проверьте логи:

```bash
# Логи скрипта
tail -f /root/vpn_bot/expired_peers.log

# Логи бота
tail -f /root/vpn_bot/vpn.log
```

### 3. Проверьте WireGuard:

```bash
# Проверить список активных peers
wg show wg0 peers

# Проверить конфиг
cat /etc/wireguard/wg0.conf | grep -A 3 "\[Peer\]"
```

---

## 📊 Пример работы:

### Пользователь с тарифом "1 месяц":

**День покупки (01.01.2025):**
- ✅ Подписка активна до: **31.01.2025**
- ✅ Конфиг доступен
- ✅ VPN работает

**Через 30 дней (01.02.2025):**
- ❌ Подписка истекла
- ❌ Скрипт ротации пароля обновляет пароль (если была ротация)
- ❌ `/myconfig` → "🌙 Подписка истекла. VPN был отключен."
- ❌ **VPN перестает работать** (старый пароль больше не работает)
- ❌ Даже если конфиг установлен на устройстве - VPN не работает

---

## ⚙️ Технические детали:

### Что делает `remove_expired_peers.py`:

1. Получает список всех пользователей с `expiry_date < текущая_дата`
2. Для каждого пользователя:
   - Удаляет peer из WireGuard интерфейса: `wg set wg0 peer <public_key> remove`
   - Удаляет секцию `[Peer]` из `/etc/wireguard/wg0.conf`
   - Деактивирует пользователя в базе: `is_active = 0`
3. Логирует все действия

### Что делает бот при `/myconfig`:

1. Проверяет `check_user_active(user_id)`
2. Если подписка истекла:
   - Вызывает `wg_manager.remove_peer_from_server(public_key)`
   - Вызывает `db.deactivate_user(user_id)`
   - Показывает сообщение: "VPN был отключен"

---

## 🎯 Итог:

### ✅ **Гарантии:**

1. **Новый конфиг получить нельзя** - бот не отдает
2. **Прямая ссылка не работает** - HTTP сервер возвращает 403
3. **VPN перестает работать** - peer удален с сервера
4. **Даже установленный конфиг не работает** - peer нет на сервере

### 📋 **Файлы для обновления на сервере:**

1. `bot.py` - добавлена автоматическая проверка при `/myconfig`
2. `wireguard.py` - улучшено удаление peer
3. `database.py` - добавлены методы `get_expired_users()` и `deactivate_user()`
4. `remove_expired_peers.py` - новый скрипт для периодической проверки

---

## 🔧 Настройка cron:

После копирования файлов на сервер:

```bash
# 1. Обновите SERVER_IP и SERVER_PUBLIC_KEY в remove_expired_peers.sh
#    (скопируйте значения из start_bot.sh)

# 2. Сделайте скрипт исполняемым
chmod +x /root/vpn_bot/remove_expired_peers.sh

# 3. Проверьте, что скрипт работает
cd /root/vpn_bot
./remove_expired_peers.sh

# 4. Добавьте в cron
crontab -e

# 5. Добавьте строку (каждый день в 3:00)
0 3 * * * /root/vpn_bot/remove_expired_peers.sh >> /root/vpn_bot/expired_peers.log 2>&1

# 6. Проверьте, что cron записал задачу
crontab -l
```

---

**Теперь VPN действительно перестает работать после истечения подписки!** ✅🔒

