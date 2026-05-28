@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Сойка VPN — получение токена ЮMoney
echo ========================================
echo.

if not exist "vpn_env\Scripts\python.exe" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ОШИБКА] Python не найден. Установите Python или создайте venv: python -m venv vpn_env
        pause
        exit /b 1
    )
    set PYTHON=python
) else (
    set PYTHON=vpn_env\Scripts\python.exe
)

if exist "yoomoney_code.txt" (
    echo Найден файл yoomoney_code.txt — обмениваю код на токен...
    echo.
    %PYTHON% yoomoney_oauth.py --file yoomoney_code.txt
) else if not "%~1"=="" (
    echo Код передан как аргумент...
    echo.
    %PYTHON% yoomoney_oauth.py "%~1"
) else (
    echo Вставьте код в файл yoomoney_code.txt ^(одной строкой^)
    echo или запустите: get_yoomoney_token.bat ВАШ_КОД
    echo.
    echo Открываю блокнот для yoomoney_code.txt ...
    echo. > yoomoney_code.txt
    notepad yoomoney_code.txt
    echo.
    echo После сохранения кода в файле нажмите любую клавишу...
    pause >nul
    if exist "yoomoney_code.txt" (
        %PYTHON% yoomoney_oauth.py --file yoomoney_code.txt
    )
)

echo.
pause
