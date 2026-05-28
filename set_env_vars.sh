#!/bin/bash
# Скрипт для быстрой установки переменных окружения на сервере
# Использование: source set_env_vars.sh

export SERVER_IP="85.234.106.239"

# 3X-UI панель (новый сервер Amsterdam)
export XUI_HOST="http://localhost:2053/K0Thd6CiSdUtkKUPif/"
export XUI_USERNAME='root'
export XUI_PASSWORD='Jv6)MKmc7(Nc'
export XUI_INBOUND_ID="1"
export XUI_SERVER_IP="$SERVER_IP"
export XUI_SNI="google.com"
export XUI_PUBLIC_KEY=""
export XUI_SHORT_ID=""
export XUI_REMARK="Netherlands"

# YooMoney
export YMONEY_ACCESS_TOKEN="4100119393589473.7E2C0ACF7B149E736BFE3C99ED8D08EA38858041FAEBCD9DE70DC7940A1CCECC99C22461C9932534B6A1E1300A0760995409D1F4C74600E98184D5B38C24D976AADDC39D6382E90E0194A2A8B71AC1904BDE3C0B3462BE6777FC1A56788F13D8BCB28D3D86423705E8589391715B198F9956444F625B815BDEB451AF870E039D"
export USE_YOOMONEY_API="false"

echo "✅ Переменные окружения установлены:"
echo "   SERVER_IP: $SERVER_IP"
echo "   XUI_HOST: $XUI_HOST"
echo "   XUI_INBOUND_ID: $XUI_INBOUND_ID"
echo ""
echo "📝 Для постоянного сохранения добавьте в ~/.bashrc:"
echo "   source ~/vpn_bot/set_env_vars.sh"

