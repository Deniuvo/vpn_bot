"""
Простой скрипт для изменения redirect_uri в yoomoney_oauth.py
"""
import os
import re

# Доступные варианты
OPTIONS = {
    "1": "https://yoomoney.ru",
    "2": "urn:ietf:wg:oauth:2.0:oob",
    "3": "http://localhost",
    "4": "Ввести свой"
}

def show_options():
    """Показать доступные варианты"""
    print("=" * 60)
    print("ВЫБОР REDIRECT URI")
    print("=" * 60)
    print("\nВыберите вариант redirect_uri:")
    print("\n1. https://yoomoney.ru (стандартный, рекомендуется)")
    print("2. urn:ietf:wg:oauth:2.0:oob (для desktop приложений)")
    print("3. http://localhost (для локальной разработки)")
    print("4. Ввести свой вариант")
    print("\n" + "=" * 60)

def change_redirect_uri_in_file(new_uri):
    """Изменить redirect_uri в файле yoomoney_oauth.py"""
    file_path = "yoomoney_oauth.py"
    
    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Находим и заменяем строку с REDIRECT_URI
        # Ищем строку вида: REDIRECT_URI = os.getenv("YOOMONEY_REDIRECT_URI", "старое_значение")
        pattern = r'REDIRECT_URI = os\.getenv\("YOOMONEY_REDIRECT_URI",\s*"[^"]*"\)'
        replacement = f'REDIRECT_URI = os.getenv("YOOMONEY_REDIRECT_URI", "{new_uri}")'
        
        new_content = re.sub(pattern, replacement, content)
        
        # Проверяем, была ли сделана замена
        if new_content == content:
            # Пробуем другой паттерн (если уже изменено)
            pattern2 = r'REDIRECT_URI\s*=\s*"[^"]*"'
            new_content = re.sub(pattern2, f'REDIRECT_URI = "{new_uri}"', content, count=1)
        
        # Записываем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"\n✅ Redirect URI успешно изменен на: {new_uri}")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при изменении файла: {e}")
        return False

def main():
    show_options()
    
    choice = input("\nВведите номер варианта (1-4): ").strip()
    
    if choice in ["1", "2", "3"]:
        new_uri = OPTIONS[choice]
        print(f"\nВыбран вариант: {new_uri}")
        
        confirm = input("\nПодтвердите изменение? (да/нет): ").strip().lower()
        if confirm in ["да", "yes", "y", "д"]:
            if change_redirect_uri_in_file(new_uri):
                print("\n" + "=" * 60)
                print("✅ Готово! Теперь можно запустить:")
                print("   python yoomoney_oauth.py")
                print("=" * 60)
            else:
                print("\n❌ Не удалось изменить файл. Попробуйте изменить вручную.")
        else:
            print("\nОтменено.")
            
    elif choice == "4":
        custom_uri = input("\nВведите свой redirect_uri: ").strip()
        if custom_uri:
            confirm = input(f"\nИзменить на '{custom_uri}'? (да/нет): ").strip().lower()
            if confirm in ["да", "yes", "y", "д"]:
                if change_redirect_uri_in_file(custom_uri):
                    print("\n" + "=" * 60)
                    print("✅ Готово! Теперь можно запустить:")
                    print("   python yoomoney_oauth.py")
                    print("=" * 60)
            else:
                print("\nОтменено.")
        else:
            print("\n❌ Redirect URI не может быть пустым!")
    else:
        print("\n❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()

