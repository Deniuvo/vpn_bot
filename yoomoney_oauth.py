"""
Модуль для получения токена доступа ЮMoney через OAuth2
Используйте этот скрипт один раз для получения токена
"""
import urllib.parse
import requests
import os
import sys

# Приложение «Сойка VPN» (кабинет ЮMoney → API → приложения)
CLIENT_ID = os.getenv(
    "YOOMONEY_CLIENT_ID",
    "8C69CB0A94C1C978C14E476A60A57B985999BFC7EEE8AC4B453BBDA45F2CF4A1",
)
CLIENT_SECRET = os.getenv("YOOMONEY_CLIENT_SECRET", "")

# Redirect URI
# ВАРИАНТЫ (выберите тот, который указан в настройках приложения в кабинете ЮMoney):
# - "urn:ietf:wg:oauth:2.0:oob" - для desktop приложений
# - "https://yoomoney.ru" - стандартный вариант (чаще всего используется)
# - "http://localhost" - для локальной разработки
# 
# ⚠️ ВАЖНО: redirect_uri должен ТОЧНО совпадать с тем, что указано в настройках приложения!
# 
# Чтобы изменить redirect_uri, вы можете:
# 1. Изменить значение ниже (замените на нужное)
# 2. Или установить переменную окружения: YOOMONEY_REDIRECT_URI="ваш_redirect_uri"
REDIRECT_URI = os.getenv("YOOMONEY_REDIRECT_URI", "https://yoomoney.ru")

# Права доступа для работы с платежами
SCOPE = "account-info operation-history operation-details incoming-transfers"


def get_authorization_url():
    """
    Получить URL для авторизации
    
    Инструкция:
    1. Запустите эту функцию
    2. Откройте полученный URL в браузере
    3. Авторизуйтесь в ЮMoney
    4. Скопируйте код из redirect URL (параметр 'code')
    5. Используйте exchange_code_for_token(code) для получения токена
    """
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }
    
    url = f"https://yoomoney.ru/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    print("=" * 60)
    print("Сойка VPN — авторизация ЮMoney")
    print("ШАГ 1: Откройте этот URL в браузере:")
    print("=" * 60)
    print(url)
    print("=" * 60)
    
    if REDIRECT_URI == "urn:ietf:wg:oauth:2.0:oob":
        print("\n[ВАЖНО] Используется специальный redirect_uri для desktop приложений")
        print("После авторизации вы увидите страницу с кодом на экране.")
        print("\nШАГ 2: Скопируйте код с экрана (или из адресной строки, если показано)")
        print("\nШАГ 3: Запустите скрипт с кодом:")
        print("python yoomoney_oauth.py ВАШ_КОД")
    else:
        print("\nШАГ 2: После авторизации вы будете перенаправлены на:")
        print(f"{REDIRECT_URI}?code=ВАШ_КОД")
        print("\nШАГ 3: Скопируйте значение параметра 'code' из URL")
        print("\nШАГ 4: Запустите скрипт с кодом:")
        print("python yoomoney_oauth.py ВАШ_КОД")
    
    print("\n[СОВЕТ] Если получили ошибку 'invalid_request':")
    print("   Проверьте, что redirect_uri в настройках приложения совпадает!")
    print(f"   Текущий redirect_uri: {REDIRECT_URI}")
    print("=" * 60)
    
    return url


def exchange_code_for_token(authorization_code: str) -> str:
    """
    Обменять authorization code на access token
    
    Args:
        authorization_code: Код авторизации из redirect URL
    
    Returns:
        Access token для использования в API
    """
    # Убираем code= из начала, если пользователь скопировал весь параметр
    if authorization_code.startswith("code="):
        authorization_code = authorization_code[5:]
    
    # Убираем redirect_uri из кода, если пользователь скопировал весь URL
    if "?" in authorization_code:
        authorization_code = authorization_code.split("?")[-1]
    if "code=" in authorization_code:
        authorization_code = authorization_code.split("code=")[-1].split("&")[0]
    
    # Определяем redirect_uri из URL, если он был передан
    actual_redirect_uri = REDIRECT_URI
    try:
        if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
            # Извлекаем redirect_uri из URL
            url_parts = sys.argv[1].split("?")[0]
            if "/main" in url_parts:
                # Если редирект был на /main, используем базовый URL (ЮMoney редиректит на /main, но в настройках должен быть базовый)
                actual_redirect_uri = "https://yoomoney.ru"
            elif url_parts.startswith("https://yoomoney.ru"):
                actual_redirect_uri = "https://yoomoney.ru"
    except (IndexError, AttributeError):
        pass
    
    # Параметры для запроса токена
    data = {
        "code": authorization_code,
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": actual_redirect_uri
    }
    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET
    
    # Отправляем запрос на получение токена
    response = requests.post("https://yoomoney.ru/oauth/token", data=data)
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        
        if not token or token == "":
            print("[ERROR] Ошибка: токен не найден в ответе или пустой")
            print(f"Ответ сервера: {result}")
            print("\nВозможные причины:")
            print("1. Код авторизации уже был использован (коды одноразовые)")
            print("2. Код авторизации истек (коды действительны несколько минут)")
            print("3. Неправильный redirect_uri")
            print("\nРешение: Получите новый код авторизации, запустив:")
            print("  python yoomoney_oauth.py")
            return None
        
        print("=" * 60)
        print("[SUCCESS] Токен успешно получен!")
        print("=" * 60)
        print(f"\nТокен доступа:\n{token}\n")
        print("=" * 60)
        print("\nСохраните этот токен!")
        print("\nДля Windows PowerShell:")
        print(f'$env:YMONEY_ACCESS_TOKEN="{token}"')
        print("\nДля Windows CMD:")
        print(f'set YMONEY_ACCESS_TOKEN={token}')
        print("\nДля Linux/Mac:")
        print(f'export YMONEY_ACCESS_TOKEN="{token}"')
        print("=" * 60)

        return token
    else:
        print("[ERROR] Ошибка при получении токена:")
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None


def _read_code_from_file(path: str) -> str:
    """Прочитать код из файла (одна строка, без пробелов по краям)."""
    with open(path, encoding="utf-8") as f:
        code = f.read().strip().replace("\n", "").replace("\r", "")
    return code


def _save_token_to_file(token: str) -> None:
    """Сохранить токен в yoomoney_token.txt и подсказку для сервера."""
    token_path = "yoomoney_token.txt"
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(token)
    print(f"\n[INFO] Токен сохранён в {token_path}")
    print("[INFO] Добавьте на сервер в start_bot.sh или ~/.bashrc:")
    print(f'export YMONEY_ACCESS_TOKEN="{token}"')
    print('export USE_YOOMONEY_API="true"')


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--file", "-f"):
        if len(sys.argv) < 3:
            print("[ERROR] Укажите файл: python yoomoney_oauth.py --file yoomoney_code.txt")
            sys.exit(1)
        code = _read_code_from_file(sys.argv[2])
        token = exchange_code_for_token(code)
        if token:
            _save_token_to_file(token)
    elif len(sys.argv) > 1:
        code = sys.argv[1]
        token = exchange_code_for_token(code)
        if token:
            _save_token_to_file(token)
    else:
        get_authorization_url()

