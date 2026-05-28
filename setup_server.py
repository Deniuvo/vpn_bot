"""
Скрипт для автоматического определения IP сервера и публичного ключа WireGuard
Запустите этот скрипт на сервере перед запуском бота
"""
import subprocess
import socket
import requests
import sys


def get_local_ip():
    """Получить локальный IP адрес сервера"""
    try:
        # Подключаемся к внешнему DNS серверу для определения внешнего IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None


def get_public_ip():
    """Получить публичный IP адрес сервера"""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except Exception:
        return None


def get_wireguard_public_key(interface="wg0"):
    """Получить публичный ключ WireGuard сервера"""
    try:
        result = subprocess.run(
            ["wg", "show", interface, "public-key"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        print("⚠️ WireGuard не установлен или команда 'wg' недоступна")
    except Exception as e:
        print(f"⚠️ Ошибка получения публичного ключа: {e}")
    
    return None


def main():
    """Главная функция"""
    print("=" * 50)
    print("Определение настроек сервера для VPN бота")
    print("=" * 50)
    
    # Определяем IP адреса
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    print(f"\n📍 Локальный IP: {local_ip or 'не определен'}")
    print(f"🌍 Публичный IP: {public_ip or 'не определен'}")
    
    # Рекомендуем использовать публичный IP
    recommended_ip = public_ip or local_ip
    
    # Получаем публичный ключ WireGuard
    wg_key = get_wireguard_public_key()
    
    print(f"\n🔑 Публичный ключ WireGuard: {wg_key or 'не определен (настройте вручную)'}")
    
    print("\n" + "=" * 50)
    print("Рекомендуемые настройки:")
    print("=" * 50)
    
    if recommended_ip:
        print(f"\nУстановите переменную окружения:")
        print(f'export SERVER_IP="{recommended_ip}"')
    
    if wg_key:
        print(f'export SERVER_PUBLIC_KEY="{wg_key}"')
    
    print("\nИли отредактируйте файл bot.py и укажите:")
    print(f'SERVER_IP = "{recommended_ip}"')
    if wg_key:
        print(f'SERVER_PUBLIC_KEY = "{wg_key}"')
    
    print("\n⚠️ ВАЖНО: Убедитесь, что:")
    print("1. Порт 51820 открыт в файрволе для WireGuard")
    print("2. Порт 5000 (или выбранный для HTTP) открыт для раздачи конфигов")
    print("3. WireGuard сервер запущен и работает")
    
    return recommended_ip, wg_key


if __name__ == '__main__':
    main()

