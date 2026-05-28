# 🔍 Проверка и исправление проблемы с peers

## Проблема

На сервере **0 peers**, хотя вы получили конфиг и подключились. Это означает, что peer не был добавлен на WireGuard сервер.

## Диагностика

### 1. Проверьте текущих peers на сервере:

```bash
wg show wg0
```

Если список пуст или нет вашего peer - проблема найдена.

### 2. Проверьте логи бота:

```bash
cd /root/vpn_bot
tail -n 100 vpn.log | grep -i peer
```

Ищите строки:
- "Добавляю peer на сервер"
- "Ошибка добавления peer"
- "Не удалось добавить peer"

## Решение

### Вариант 1: Автоматическое добавление через бота (рекомендуется)

1. Получите ваш конфиг еще раз через `/myconfig`
2. Проверьте логи бота - возможно, peer добавится автоматически
3. Если ошибка повторяется, используйте вариант 2

### Вариант 2: Ручное добавление peer

1. **Получите ваш Public Key из конфига:**

Откройте файл конфига (который вы получили от бота) и найдите строку:
```
PrivateKey = <ваш_приватный_ключ>
```

Или если у вас есть доступ к базе данных бота, получите из базы.

2. **Узнайте ваш IP адрес:**

Из конфига найдите строку:
```
Address = 10.0.0.X/32
```

Или из базы данных бота.

3. **Добавьте peer вручную:**

```bash
# Замените значения на ваши!
PUBLIC_KEY="ваш_публичный_ключ"
IP_ADDRESS="10.0.0.5"  # ваш IP из конфига

wg set wg0 peer "$PUBLIC_KEY" allowed-ips "${IP_ADDRESS}/32"
```

4. **Проверьте:**

```bash
wg show wg0
```

Ваш peer должен появиться в списке.

### Вариант 3: Использование скрипта

```bash
cd /root/vpn_bot
chmod +x fix_peer_manual.sh
./fix_peer_manual.sh <PUBLIC_KEY> <IP_ADDRESS>
```

## Получение данных из базы данных бота

Если нужно найти ваш Public Key и IP:

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 << EOF
from database import db

# Замените на ваш user_id из Telegram
user_id = YOUR_TELEGRAM_USER_ID

user_data = db.get_user(user_id)
if user_data:
    print(f"IP Address: {user_data['ip_address']}")
    print(f"Public Key: {user_data['public_key']}")
    print(f"Private Key: {user_data['private_key']}")
else:
    print("Пользователь не найден в базе")
EOF
```

## Важно: Сохранение peer в конфиг

После перезапуска WireGuard peer может исчезнуть, если он не сохранен в `/etc/wireguard/wg0.conf`.

Чтобы сохранить peer постоянно, добавьте в конец `/etc/wireguard/wg0.conf`:

```ini
[Peer]
PublicKey = ваш_публичный_ключ
AllowedIPs = 10.0.0.X/32
```

Затем перезапустите WireGuard:
```bash
wg-quick down wg0
wg-quick up wg0
```

## Проверка после исправления

1. **На сервере:**
```bash
wg show wg0
# Должен показать вашего peer
```

2. **На клиенте:**
   - Подключите VPN в WireGuard
   - Откройте https://ifconfig.me
   - Должен показать IP вашего сервера

3. **Проверка трафика:**
```bash
# На сервере - смотрим передачу данных
wg show wg0 transfer
```

Если видите передачу данных - VPN работает!

## Если проблема сохраняется

1. Проверьте, что бот имеет права на выполнение команды `wg`
2. Проверьте логи бота на наличие ошибок
3. Убедитесь, что WireGuard запущен: `systemctl status wg-quick@wg0`
4. Попробуйте перезапустить WireGuard: `wg-quick down wg0 && wg-quick up wg0`

