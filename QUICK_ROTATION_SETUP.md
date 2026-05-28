# ⚡ БЫСТРАЯ НАСТРОЙКА: Ротация пароля Shadowsocks

## 🚀 За 3 шага:

### Шаг 1: Скопируйте файлы на сервер

```bash
# С вашего компьютера
scp rotate_shadowsocks_password.py rotate_password.sh shadowsocks_manager.py root@ваш_сервер:/root/vpn_bot/
```

### Шаг 2: На сервере - тест

```bash
ssh root@ваш_сервер
cd /root/vpn_bot
chmod +x rotate_password.sh
source vpn_env/bin/activate
export SERVER_IP="ваш_ip"  # Замените на реальный IP
python3 rotate_shadowsocks_password.py
```

### Шаг 3: Настройка авто-запуска

```bash
crontab -e
# Добавьте строку (каждый месяц 1-го числа в 3:00):
0 3 1 * * /root/vpn_bot/rotate_password.sh >> /root/vpn_bot/password_rotation.log 2>&1
```

**Готово!** 🎉

---

## ✅ Проверка:

```bash
# Проверьте что задача добавлена
crontab -l

# Проверьте логи
tail -f password_rotation.log
```

**Подробная инструкция:** См. `PASSWORD_ROTATION_SETUP.md`

