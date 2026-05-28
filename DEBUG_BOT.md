# 🔍 Диагностика проблем с ботом

Если бот запущен, но не отвечает на команды, выполните эти шаги:

## 1. Проверьте логи бота

```bash
cd /root/vpn_bot
tail -n 100 vpn.log
```

Или в реальном времени:
```bash
tail -f vpn.log
```

## 2. Проверьте, что процесс бота запущен

```bash
ps aux | grep python3 | grep main.py
```

Должен быть процесс с `python3 main.py`.

## 3. Запустите диагностический скрипт

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
python3 check_bot.py
```

Этот скрипт проверит:
- ✅ Установлены ли все зависимости
- ✅ Существуют ли все файлы
- ✅ Настроены ли переменные окружения
- ✅ Правильный ли синтаксис в bot.py

## 4. Проверьте установку qrcode

Если в логах есть ошибка `No module named 'qrcode'`:

```bash
cd /root/vpn_bot
source vpn_env/bin/activate
pip install qrcode[pil]==7.4.2
```

## 5. Проверьте переменные окружения

```bash
echo $SERVER_IP
echo $YMONEY_ACCESS_TOKEN
echo $USE_YOOMONEY_API
```

Если они пустые, установите их:
```bash
export SERVER_IP="90.156.169.27"
export SERVER_PUBLIC_KEY="LOn7s/VtqgAIWD9Ibu2rLoxC1zvcoIg+Ln7gx5LTB0Y="
export YMONEY_ACCESS_TOKEN="ваш_токен"
export USE_YOOMONEY_API="true"
```

## 6. Перезапустите бота

Сначала остановите старый процесс:
```bash
pkill -f "python3 main.py"
```

Затем запустите заново:
```bash
cd /root/vpn_bot
bash start_bot.sh
```

Или вручную:
```bash
cd /root/vpn_bot
source vpn_env/bin/activate
export SERVER_IP="90.156.169.27"
export SERVER_PUBLIC_KEY="LOn7s/VtqgAIWD9Ibu2rLoxC1zvcoIg+Ln7gx5LTB0Y="
export YMONEY_ACCESS_TOKEN="ваш_токен"
export USE_YOOMONEY_API="true"
nohup python3 main.py > vpn.log 2>&1 &
```

## 7. Проверьте токен бота

Убедитесь, что токен в `bot.py` правильный:
```bash
grep "BOT_TOKEN" bot.py
```

## 8. Проверьте, что бот запустился без ошибок

После запуска подождите 5 секунд и проверьте логи:
```bash
tail -n 50 vpn.log
```

Должна быть строка: `✅ Бот запущен...` или `Бот запущен...`

Если видите ошибки - скопируйте их и сообщите разработчику.

## Частые проблемы:

### ❌ `ModuleNotFoundError: No module named 'qrcode'`
**Решение:** 
```bash
source vpn_env/bin/activate
pip install qrcode[pil]==7.4.2
```

### ❌ `❌ ОШИБКА: Не настроен IP сервера!`
**Решение:** Установите переменную окружения:
```bash
export SERVER_IP="ваш_ip"
```

### ❌ Бот запускается, но сразу падает
**Решение:** Проверьте логи - там будет причина ошибки.

### ❌ Бот работает, но не отвечает на команды
**Решение:** 
1. Проверьте, правильный ли токен бота в `bot.py`
2. Убедитесь, что пишете правильному боту в Telegram
3. Проверьте логи на наличие ошибок обработки команд

## Быстрая диагностика одной командой:

```bash
cd /root/vpn_bot && source vpn_env/bin/activate && python3 check_bot.py && tail -n 30 vpn.log
```

Это выполнит все проверки и покажет последние логи.

