#!/usr/bin/env python3
"""
Скрипт для проверки работоспособности бота и его зависимостей
"""
import sys
import os

print("🔍 Проверка зависимостей бота...\n")

errors = []
warnings = []

# Проверка Python версии
if sys.version_info < (3, 7):
    errors.append(f"❌ Python версия слишком старая: {sys.version}")
else:
    print(f"✅ Python версия: {sys.version}")

# Проверка импортов
modules = [
    ('telegram', 'python-telegram-bot'),
    ('cryptography', 'cryptography'),
    ('flask', 'flask'),
    ('requests', 'requests'),
    ('yoomoney', 'yoomoney'),
    ('qrcode', 'qrcode[pil]'),
    ('PIL', 'Pillow (для qrcode)'),
]

for module_name, package_name in modules:
    try:
        if module_name == 'telegram':
            from telegram import Update
        elif module_name == 'qrcode':
            import qrcode
        elif module_name == 'PIL':
            from PIL import Image
        else:
            __import__(module_name)
        print(f"✅ {package_name} установлен")
    except ImportError as e:
        errors.append(f"❌ {package_name} НЕ установлен: {e}")
        print(f"❌ {package_name} НЕ установлен")

# Проверка файлов
files_to_check = [
    'bot.py',
    'database.py',
    'wireguard.py',
    'config_server.py',
    'yoomoney_api.py',
]

print("\n📁 Проверка файлов...")
for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file} существует")
    else:
        errors.append(f"❌ Файл {file} не найден")
        print(f"❌ {file} не найден")

# Проверка директорий
dirs_to_check = ['configs']
print("\n📂 Проверка директорий...")
for dir_name in dirs_to_check:
    if os.path.exists(dir_name):
        print(f"✅ Директория {dir_name} существует")
    else:
        warnings.append(f"⚠️ Директория {dir_name} не существует (будет создана автоматически)")
        print(f"⚠️ Директория {dir_name} не существует (будет создана автоматически)")

# Проверка переменных окружения
print("\n🔧 Проверка переменных окружения...")
env_vars = {
    'SERVER_IP': os.getenv('SERVER_IP'),
    'SERVER_PUBLIC_KEY': os.getenv('SERVER_PUBLIC_KEY'),
    'YMONEY_ACCESS_TOKEN': os.getenv('YMONEY_ACCESS_TOKEN'),
    'USE_YOOMONEY_API': os.getenv('USE_YOOMONEY_API'),
}

for var_name, var_value in env_vars.items():
    if var_value:
        if var_name == 'YMONEY_ACCESS_TOKEN':
            print(f"✅ {var_name} установлен (длина: {len(var_value)} символов)")
        elif var_name == 'USE_YOOMONEY_API':
            print(f"✅ {var_name} = {var_value}")
        else:
            print(f"✅ {var_name} = {var_value}")
    else:
        if var_name == 'SERVER_PUBLIC_KEY':
            warnings.append(f"⚠️ {var_name} не установлен (опционально)")
            print(f"⚠️ {var_name} не установлен (опционально)")
        elif var_name == 'SERVER_IP':
            errors.append(f"❌ {var_name} не установлен (ОБЯЗАТЕЛЬНО!)")
            print(f"❌ {var_name} не установлен (ОБЯЗАТЕЛЬНО!)")
        else:
            warnings.append(f"⚠️ {var_name} не установлен")
            print(f"⚠️ {var_name} не установлен")

# Проверка синтаксиса bot.py
print("\n🐍 Проверка синтаксиса bot.py...")
try:
    with open('bot.py', 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, 'bot.py', 'exec')
    print("✅ Синтаксис bot.py корректен")
except SyntaxError as e:
    errors.append(f"❌ Синтаксическая ошибка в bot.py: {e}")
    print(f"❌ Синтаксическая ошибка в bot.py: {e}")

# Итоги
print("\n" + "="*50)
if errors:
    print("❌ ОШИБКИ (бот не запустится):")
    for error in errors:
        print(f"  {error}")
else:
    print("✅ Критических ошибок не найдено!")

if warnings:
    print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
    for warning in warnings:
        print(f"  {warning}")

if not errors:
    print("\n✅ Все основные проверки пройдены!")
    print("💡 Если бот все еще не отвечает, проверьте логи:")
    print("   tail -f /root/vpn_bot/vpn.log")
else:
    print("\n❌ Исправьте ошибки перед запуском бота!")
    sys.exit(1)

