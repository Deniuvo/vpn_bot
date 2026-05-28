#!/bin/bash
# Сойка VPN — обмен OAuth-кода ЮMoney на access token
cd "$(dirname "$0")"

echo "========================================"
echo "  Сойка VPN — получение токена ЮMoney"
echo "========================================"
echo

if [ -f "vpn_env/bin/activate" ]; then
    source vpn_env/bin/activate
fi

if [ -n "$1" ]; then
    python3 yoomoney_oauth.py "$1"
elif [ -f "yoomoney_code.txt" ]; then
    echo "Читаю код из yoomoney_code.txt..."
    python3 yoomoney_oauth.py --file yoomoney_code.txt
else
    echo "Вставьте код в yoomoney_code.txt (одной строкой) и запустите снова."
    echo "Или: ./get_yoomoney_token.sh ВАШ_КОД"
    touch yoomoney_code.txt
    "${EDITOR:-nano}" yoomoney_code.txt
    python3 yoomoney_oauth.py --file yoomoney_code.txt
fi
