#!/bin/bash
source /root/vpn_bot/.env
curl -s -H "Authorization: Bearer $YMONEY_ACCESS_TOKEN" \
  https://yoomoney.ru/api/account-info | head -c 200
echo
