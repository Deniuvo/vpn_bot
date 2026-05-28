"""
Модуль для интеграции с CryptoCloud API v2
Прием платежей в криптовалюте
"""
import os
import logging
import requests
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

CRYPTOCLOUD_API_KEY = os.getenv(
    "CRYPTOCLOUD_API_KEY",
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1dWlkIjoiTVRBek1qZzEiLCJ0eXBlIjoicHJvamVjdCIsInYiOiI5ZTZkN2ZjY2UzMDZhYjU3YTc5NGFmNjNhN2JmODgyYWI4ZTcxNjUwN2JmYzUxZWRkZDJkZjFhYmZkOWNhYTAyIiwiZXhwIjo4ODE3OTg4NTcxNX0.e7kU8iQTZPO2Il0KnYnhEaT41vFXtZDLdEr7uvqh00s"
)
CRYPTOCLOUD_SHOP_ID = os.getenv("CRYPTOCLOUD_SHOP_ID", "YPrRnU68z7Lrc7G4")
CRYPTOCLOUD_SECRET = os.getenv("CRYPTOCLOUD_SECRET", "2zckVOgcWOGLseYPF9jVQ3B29HopsFVIzva5")

API_BASE = "https://api.cryptocloud.plus/v2"


class CryptoCloudAPI:
    """Клиент для работы с CryptoCloud API v2"""

    def __init__(self):
        self.api_key = CRYPTOCLOUD_API_KEY
        self.shop_id = CRYPTOCLOUD_SHOP_ID
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        })

    def create_invoice(self, amount: float, order_id: str, currency: str = "USD",
                       email: str = None, cryptocurrency: str = None) -> dict:
        """
        Создать счет (invoice) на оплату

        Args:
            amount: Сумма в USD
            order_id: Уникальный номер заказа (user_id + tariff)
            currency: Валюта счета (USD по умолчанию)
            email: Email плательщика
            cryptocurrency: Конкретная криптовалюта для оплаты

        Returns:
            dict: Ответ API с ссылкой на оплату
        """
        payload = {
            "shop_id": self.shop_id,
            "amount": amount,
            "currency": currency,
            "order_id": order_id,
        }

        add_fields = {}
        if email:
            add_fields["email"] = email
        if cryptocurrency:
            add_fields["cryptocurrency"] = cryptocurrency
        if add_fields:
            payload["add_fields"] = add_fields

        try:
            resp = self.session.post(
                f"{API_BASE}/invoice/create",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                logger.info(f"CryptoCloud invoice created: uuid={result.get('uuid')}, link={result.get('link')}")
                return result
            else:
                logger.error(f"CryptoCloud error: {data}")
                return None
        except Exception as e:
            logger.error(f"CryptoCloud create_invoice error: {e}")
            return None

    def get_invoice_info(self, invoice_uuid: str) -> dict:
        """Получить информацию о счете"""
        try:
            resp = self.session.get(
                f"{API_BASE}/invoice/info",
                params={"uuid": invoice_uuid},
                timeout=15
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"CryptoCloud get_invoice_info error: {e}")
            return None


cryptocloud = CryptoCloudAPI()


def create_cryptocloud_order_id(user_id: int, tariff_type: str) -> str:
    """Генерирует уникальный order_id для CryptoCloud"""
    return f"vpn_{user_id}_{tariff_type}_{int(datetime.now().timestamp())}"
