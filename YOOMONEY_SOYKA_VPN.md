# ЮMoney для «Сойка VPN»

Подключение автоматической проверки оплат в боте.

## Данные приложения

| Параметр | Значение |
|----------|----------|
| Название | Сойка VPN |
| client_id | `FF72E621F882081F4C017BD0F74C63EB9E5E731C4F40D104EEF5C9712D33188C` |
| client_secret | (в `bot.py` / переменной `YOOMONEY_CLIENT_SECRET`) |
| Кошелёк для приёма | `4100119393589473` (в `YMONEY_WALLET`) |

Код бота уже обновлён под эти `client_id` и `client_secret`.

---

## Шаг 1. Настройки в кабинете ЮMoney

1. Откройте [yoomoney.ru](https://yoomoney.ru) → войдите в кошелёк **4100119393589473**.
2. **Настройки** → **API** → приложение **«Сойка VPN»**.
3. **Redirect URI** — должен **точно совпадать** с тем, что в скрипте. По умолчанию:
   ```
   https://yoomoney.ru
   ```
   Если в кабинете указан другой URI — задайте его в `yoomoney_oauth.py` или:
   ```bash
   export YOOMONEY_REDIRECT_URI="ваш_uri_из_кабинета"
   ```
4. Включите права (scope):
   - `account-info`
   - `operation-history`
   - `operation-details`
   - `incoming-transfers`

---

## Шаг 2. Получить access token (один раз)

На компьютере или на сервере в папке проекта:

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
pip install requests
python yoomoney_oauth.py
```

1. Скопируйте URL из вывода и откройте в браузере.
2. Войдите в ЮMoney и нажмите **Разрешить**.
3. Из адресной строки после редиректа скопируйте параметр `code=...`
   (пример: `https://yoomoney.ru?code=XXXXXXXX`).
4. Обменяйте код на токен — **без длинной команды вручную:**

**Windows:** дважды щёлкните `get_yoomoney_token.bat`  
(код положите в файл `yoomoney_code.txt` одной строкой)

**Или PowerShell:**
```powershell
.\get_yoomoney_token.ps1
```

**Linux / сервер:**
```bash
chmod +x get_yoomoney_token.sh
# код в yoomoney_code.txt, затем:
./get_yoomoney_token.sh
```

Токен сохранится в `yoomoney_token.txt` и будет выведен в консоль.

> Код авторизации одноразовый и живёт несколько минут. При ошибке запустите `python yoomoney_oauth.py` снова.

---

## Шаг 3. Указать токен на сервере

```bash
export YMONEY_ACCESS_TOKEN="токен_из_шага_2"
export USE_YOOMONEY_API="true"
```

Постоянно (после перезагрузки сервера):

```bash
echo 'export YMONEY_ACCESS_TOKEN="ваш_токен"' >> ~/.bashrc
echo 'export USE_YOOMONEY_API="true"' >> ~/.bashrc
source ~/.bashrc
```

Или в `start_bot.sh` / systemd — добавьте те же переменные.

---

## Шаг 4. Перезапустить бота

```bash
pkill -f "python3 main.py"
cd /root/vpn_bot
source vpn_env/bin/activate
export SERVER_IP="ваш_ip"
export YMONEY_ACCESS_TOKEN="ваш_токен"
export USE_YOOMONEY_API="true"
nohup python3 main.py > vpn.log 2>&1 &
tail -f vpn.log
```

В логе должно быть:
```
✅ Токен API ЮMoney установлен. Автоматическая проверка платежей включена.
```

Если видите предупреждение про отсутствие токена — `YMONEY_ACCESS_TOKEN` не задан в окружении процесса бота.

---

## Проверка

1. В боте: `/buy` → выберите тариф → **Перейти к оплате**.
2. Оплатите тестовую сумму на кошелёк с **комментарием**, который покажет бот.
3. Нажмите **Проверить оплату** — должен прийти конфиг.

Проверка токена:

```bash
python -c "from yoomoney_api import YooMoneyAPI; import os; t=os.getenv('YMONEY_ACCESS_TOKEN'); print('OK' if t and YooMoneyAPI(t).get_account_info() else 'FAIL')"
```

---

## Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `invalid_request` при OAuth | Redirect URI в кабинете ≠ в скрипте |
| Платёж не находится | Подождите 1–2 мин; проверьте сумму и комментарий |
| Старый токен | После смены приложения нужен **новый** токен через `yoomoney_oauth.py` |
| Бот без API | `USE_YOOMONEY_API=false` или нет `YMONEY_ACCESS_TOKEN` |

Подробнее: `FIX_OAUTH_ERROR.md`, `GET_TOKEN.md`.
