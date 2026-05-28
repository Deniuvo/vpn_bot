# Установка и настройка 3X-UI на сервере

## 1. Установка 3X-UI

```bash
# Подключитесь к серверу по SSH
ssh root@90.156.169.27

# Установите 3X-UI (одна команда)
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

При установке:
- Задайте **логин** и **пароль** для панели (запомните их!)
- Порт панели по умолчанию: **2053**

## 2. Настройка VLESS+Reality inbound

1. Откройте панель в браузере: `http://YOUR_SERVER_IP:2053`
2. Войдите с логином/паролем
3. Перейдите в **Inbounds** → **Add Inbound**
4. Настройте:
   - **Remark:** SoykaVPN
   - **Protocol:** vless
   - **Port:** 443
   - **Transmission:** tcp
   - **Security:** reality
   - **uTLS:** chrome
   - **Dest:** www.google.com:443
   - **SNI:** www.google.com
   - Нажмите **Generate** для Reality ключей
5. Сохраните inbound

## 3. Настройка переменных окружения

Отредактируйте `set_env_vars.sh` на сервере:

```bash
export XUI_HOST="http://localhost:2053"      # URL панели 3X-UI
export XUI_USERNAME="ваш_логин"              # Логин от панели
export XUI_PASSWORD="ваш_пароль"             # Пароль от панели
export XUI_INBOUND_ID="1"                    # ID inbound (обычно 1 для первого)
export XUI_SERVER_IP="90.156.169.27"         # IP вашего сервера
export XUI_SERVER_PORT="443"                 # Порт inbound
export XUI_SNI="www.google.com"              # SNI из настроек Reality
```

Затем:
```bash
source set_env_vars.sh
```

## 4. Установка зависимостей бота

```bash
cd ~/vpn_bot
pip install -r requirements.txt
```

## 5. Запуск бота

```bash
source set_env_vars.sh
python bot.py
```

## 6. Проверка

- Бот должен сказать `✅ 3X-UI менеджер инициализирован`
- Купите тариф — бот создаст клиента в 3X-UI и отправит vless:// ссылку
- Откройте Happ → отсканируйте QR или вставьте ссылку

## Важно

- **Порт 443** должен быть открыт в firewall сервера
- **Порт 2053** (панель) лучше закрыть от внешнего доступа или сменить
- Не забудьте сменить пароль по умолчанию в панели 3X-UI
- WireGuard можно удалить: `wg-quick down wg0 && apt remove wireguard -y`
