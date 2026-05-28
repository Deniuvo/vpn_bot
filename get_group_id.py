#!/usr/bin/env python3
"""
Скрипт для получения ID админской группы
Использование: python3 get_group_id.py
"""

import os
from telegram import Bot

BOT_TOKEN = "8975004514:AAGCCRTwuIFBI5d5Pn2ZByJJplGGxHIOL2M"

def get_group_id():
    """Получить ID группы из последних обновлений"""
    bot = Bot(token=BOT_TOKEN)
    
    print("🔍 Ищу группу в последних обновлениях...")
    print("💡 Совет: Отправьте сообщение в группу @winxvpn_admin, затем запустите этот скрипт\n")
    
    try:
        updates = bot.get_updates(limit=10)
        groups_found = []
        
        for update in updates:
            if update.message and update.message.chat.type in ['group', 'supergroup']:
                chat = update.message.chat
                if chat.id not in [g['id'] for g in groups_found]:
                    groups_found.append({
                        'id': chat.id,
                        'title': chat.title or 'Без названия',
                        'username': chat.username or 'Нет username'
                    })
        
        if groups_found:
            print("✅ Найдены группы:\n")
            for group in groups_found:
                print(f"📢 Название: {group['title']}")
                print(f"   Username: @{group['username']}" if group['username'] != 'Нет username' else "   Username: Нет")
                print(f"   ID группы: {group['id']}")
                print(f"   Команда для установки:")
                print(f"   export ADMIN_CHAT_ID=\"{group['id']}\"")
                print()
        else:
            print("❌ Группы не найдены в последних обновлениях")
            print("\n💡 Как получить ID группы:")
            print("1. Добавьте бота @userinfobot в группу")
            print("2. Отправьте /start в группе")
            print("3. Бот покажет ID группы")
            print("\nИли используйте бота @RawDataBot")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Убедитесь, что:")
        print("- Бот запущен")
        print("- Бот добавлен в группу")
        print("- Вы отправили сообщение в группу")

if __name__ == "__main__":
    get_group_id()

