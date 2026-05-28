#!/usr/bin/env python3
"""
Скрипт для поиска peer'ов в базе данных и добавления их на WireGuard сервер
"""
import sqlite3
import subprocess
import sys
import os

# Путь к базе данных
DB_PATH = "vpn_bot.db"

def get_all_users():
    """Получить всех пользователей из базы данных"""
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных {DB_PATH} не найдена!")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, ip_address, public_key, subscription_type
        FROM users
        ORDER BY user_id
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    return users

def add_peer(public_key, ip_address):
    """Добавить peer на WireGuard сервер"""
    try:
        cmd = ["wg", "set", "wg0", "peer", public_key, "allowed-ips", f"{ip_address}/32"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True, None
        else:
            error = result.stderr.strip() if result.stderr else result.stdout.strip()
            return False, error
    except Exception as e:
        return False, str(e)

def check_peer_exists(public_key):
    """Проверить, существует ли peer на сервере"""
    try:
        result = subprocess.run(["wg", "show", "wg0", "peers"], 
                              capture_output=True, text=True, timeout=5)
        return public_key in result.stdout
    except:
        return False

def main():
    print("🔍 Поиск пользователей в базе данных...")
    print("=" * 60)
    
    users = get_all_users()
    
    if not users:
        print("❌ Пользователи не найдены в базе данных!")
        return
    
    print(f"📊 Найдено пользователей: {len(users)}\n")
    
    # Показываем всех пользователей
    print("📋 Список пользователей:")
    print("-" * 60)
    for i, (user_id, username, ip_address, public_key, sub_type) in enumerate(users, 1):
        exists = check_peer_exists(public_key) if public_key else False
        status = "✅ На сервере" if exists else "❌ НЕ на сервере"
        print(f"{i}. User ID: {user_id}")
        print(f"   Username: {username or 'N/A'}")
        print(f"   IP: {ip_address}")
        print(f"   Подписка: {sub_type}")
        print(f"   Статус: {status}")
        if public_key:
            print(f"   Public Key: {public_key[:30]}...")
        print()
    
    print("=" * 60)
    print()
    
    # Спрашиваем, кого добавить
    print("💡 Выберите действие:")
    print("   1. Добавить всех пользователей на сервер")
    print("   2. Добавить конкретного пользователя")
    print("   3. Показать только тех, кто не на сервере")
    print("   0. Выход")
    
    choice = input("\nВаш выбор: ").strip()
    
    if choice == "0":
        return
    elif choice == "1":
        # Добавляем всех
        print("\n🔧 Добавляю всех пользователей на сервер...")
        added = 0
        failed = 0
        
        for user_id, username, ip_address, public_key, sub_type in users:
            if not public_key or not ip_address:
                print(f"⚠️ Пропуск user_id={user_id}: нет данных")
                continue
            
            if check_peer_exists(public_key):
                print(f"✅ User {user_id} уже на сервере")
                continue
            
            print(f"Добавляю user_id={user_id}, IP={ip_address}...", end=" ")
            success, error = add_peer(public_key, ip_address)
            
            if success:
                print("✅")
                added += 1
            else:
                print(f"❌ Ошибка: {error}")
                failed += 1
        
        print(f"\n📊 Результат: добавлено {added}, ошибок {failed}")
        
    elif choice == "2":
        # Добавляем конкретного
        user_id = input("Введите User ID: ").strip()
        
        user = None
        for u in users:
            if str(u[0]) == user_id:
                user = u
                break
        
        if not user:
            print(f"❌ Пользователь {user_id} не найден!")
            return
        
        _, username, ip_address, public_key, sub_type = user
        
        if not public_key or not ip_address:
            print(f"❌ У пользователя нет данных (IP или Public Key)!")
            return
        
        if check_peer_exists(public_key):
            print(f"✅ Peer уже на сервере!")
            return
        
        print(f"\n🔧 Добавляю peer...")
        print(f"   User ID: {user_id}")
        print(f"   IP: {ip_address}")
        print(f"   Public Key: {public_key[:30]}...")
        
        success, error = add_peer(public_key, ip_address)
        
        if success:
            print("✅ Peer успешно добавлен!")
            
            # Проверяем
            if check_peer_exists(public_key):
                print("✅ Peer подтвержден на сервере!")
            else:
                print("⚠️ Peer добавлен, но не найден при проверке")
        else:
            print(f"❌ Ошибка: {error}")
            
    elif choice == "3":
        # Показываем только тех, кто не на сервере
        print("\n❌ Пользователи, НЕ добавленные на сервер:")
        print("-" * 60)
        
        missing = []
        for user_id, username, ip_address, public_key, sub_type in users:
            if not public_key or not ip_address:
                continue
            
            if not check_peer_exists(public_key):
                missing.append((user_id, username, ip_address, public_key))
                print(f"   User ID: {user_id}, Username: {username}, IP: {ip_address}")
        
        if not missing:
            print("   ✅ Все пользователи на сервере!")
        else:
            print(f"\n📊 Всего не на сервере: {len(missing)}")
            print("\n💡 Запустите скрипт снова и выберите опцию 1 для добавления всех")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

