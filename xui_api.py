"""
Модуль для работы с 3X-UI API
Использует py3xui для авторизации (JWT cookie + CSRF), затем прямые HTTP-запросы
Автоматически читает настройки inbound (port, realitySettings) для генерации ссылок
"""
import os
import json
import uuid
import time
import logging
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

XUI_HOST = os.getenv("XUI_HOST", "http://localhost:2053")
XUI_USERNAME = os.getenv("XUI_USERNAME", "admin")
XUI_PASSWORD = os.getenv("XUI_PASSWORD", "admin")
XUI_INBOUND_ID = int(os.getenv("XUI_INBOUND_ID", "1"))
XUI_SERVER_IP = os.getenv("XUI_SERVER_IP", "127.0.0.1")
XUI_SUB_URL = os.getenv("XUI_SUB_URL", "")

# Fallback publicKey / shortId (можно задать вручную если API не отдаёт)
XUI_PUBLIC_KEY = os.getenv("XUI_PUBLIC_KEY", "")
XUI_SHORT_ID = os.getenv("XUI_SHORT_ID", "")
XUI_REMARK = os.getenv("XUI_REMARK", "")

try:
    from py3xui import Api
    PY3XUI_AVAILABLE = True
except ImportError:
    PY3XUI_AVAILABLE = False
    logger.warning("py3xui не установлен. Авторизация невозможна.")


class XUIManager:
    """Управление 3X-UI: py3xui auth + direct HTTP для клиентских операций"""

    def __init__(self):
        self._api = None
        self._session = ""
        self._csrf = ""
        self._cookies = {}
        self._logged_in = False
        # Кэш inbound-настроек для генерации ссылок
        self._inbound_cache = None

    def _ensure_login(self) -> bool:
        if self._logged_in:
            return True
        try:
            if not PY3XUI_AVAILABLE:
                logger.error("py3xui не доступен")
                return False
            self._api = Api(XUI_HOST, XUI_USERNAME, XUI_PASSWORD, use_tls_verify=False)
            self._api.login()
            self._session = getattr(self._api, '_session', '')
            self._csrf = getattr(self._api, '_csrf_token', '')
            self._cookies = {'3x-ui': self._session} if self._session else {}
            self._logged_in = True
            logger.info("✅ Авторизация в 3X-UI успешна (py3xui)")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка авторизации в 3X-UI: {e}")
            self._logged_in = False
            return False

    def _request(self, method: str, path: str, **kwargs):
        """HTTP-запрос с JWT cookie и CSRF-токеном"""
        self._ensure_login()
        url = f"{XUI_HOST.rstrip('/')}/{path.lstrip('/')}".replace('//', '/').replace(':/', '://')
        headers = kwargs.pop('headers', {})
        headers['Accept'] = 'application/json'
        if self._csrf:
            headers['X-CSRF-Token'] = self._csrf
        s = requests.Session()
        s.verify = False
        s.cookies.update(self._cookies)
        return s.request(method, url, headers=headers, timeout=30, **kwargs)

    @staticmethod
    def _parse_settings(raw):
        if raw is None:
            return {"clients": [], "decryption": "none", "fallbacks": []}
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)

    @staticmethod
    def _parse_json_field(raw):
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except:
            return {}

    def _get_inbound_raw(self, inbound_id: int = None) -> dict:
        iid = inbound_id or XUI_INBOUND_ID
        resp = self._request('GET', f'/panel/api/inbounds/get/{iid}')
        data = resp.json()
        if not data.get('success'):
            raise Exception(data.get('msg', 'Failed to get inbound'))
        obj = data.get('obj', {})
        obj['settings'] = self._parse_settings(obj.get('settings'))
        obj['streamSettings'] = self._parse_json_field(obj.get('streamSettings'))
        obj['sniffing'] = self._parse_json_field(obj.get('sniffing'))
        return obj

    def _update_inbound(self, obj: dict, inbound_id: int = None) -> bool:
        iid = inbound_id or XUI_INBOUND_ID
        payload = {
            "id": obj.get("id"),
            "remark": obj.get("remark", ""),
            "enable": obj.get("enable", True),
            "listen": obj.get("listen", ""),
            "port": obj.get("port", 443),
            "protocol": obj.get("protocol", "vless"),
            "tag": obj.get("tag", ""),
            "settings": obj.get("settings", {"clients": []}),
            "streamSettings": obj.get("streamSettings", {}),
            "sniffing": obj.get("sniffing", {}),
        }
        resp = self._request('POST', f'/panel/api/inbounds/update/{iid}', json=payload)
        if resp.status_code >= 400:
            logger.error(f"❌ update inbound {iid}: status={resp.status_code}, body={resp.text[:200]!r}")
            return False
        try:
            data = resp.json()
            if not data.get('success'):
                logger.error(f"❌ update inbound {iid}: {data.get('msg')}")
                return False
        except:
            pass
        logger.info(f"✅ Inbound {iid} обновлён")
        return True

    def _get_all_inbound_ids(self) -> list:
        """Получить список всех inbound ID"""
        try:
            resp = self._request('GET', '/panel/api/inbounds/list')
            data = resp.json()
            if not data.get('success'):
                logger.warning(f"Не удалось получить список inbound: {data.get('msg')}")
                return [XUI_INBOUND_ID]
            objs = data.get('obj', [])
            return [obj.get('id', XUI_INBOUND_ID) for obj in objs if obj.get('enable', True)]
        except Exception as e:
            logger.error(f"Ошибка получения списка inbound: {e}")
            return [XUI_INBOUND_ID]

    # ============== Public CRUD ==============

    def create_client(self, user_id: int, email: str, expiry_days: int, remark: str = None) -> dict:
        self._ensure_login()
        try:
            inbound_ids = self._get_all_inbound_ids()
            client_uuid = str(uuid.uuid4())
            exp_ts = int((time.time() + expiry_days * 86400) * 1000)
            new_client = {
                "id": client_uuid,
                "email": email,
                "enable": True,
                "expiryTime": exp_ts,
                "totalGB": 0,
                "flow": "xtls-rprx-vision",
                "limitIp": 3,
                "tgId": "",
                "subId": email,
                "remark": remark or "CloudHapp",
            }

            for iid in inbound_ids:
                try:
                    obj = self._get_inbound_raw(iid)
                    settings = obj.get('settings', {})
                    clients = settings.setdefault('clients', [])
                    # Удаляем старого клиента с тем же email
                    before = len(clients)
                    clients[:] = [c for c in clients if c.get('email') != email]
                    if len(clients) < before:
                        logger.info(f"Удалён старый клиент с email={email} из inbound {iid}")
                    clients.append(new_client.copy())
                    if not self._update_inbound(obj, iid):
                        logger.warning(f"⚠️ Не удалось обновить inbound {iid}")
                    else:
                        logger.info(f"✅ Клиент добавлен в inbound {iid}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка inbound {iid}: {e}")

            logger.info(f"✅ Клиент создан: uuid={client_uuid[:8]}..., email={email}, inbounds={len(inbound_ids)}")
            return {"uuid": client_uuid, "email": email}
        except Exception as e:
            logger.error(f"❌ Ошибка создания клиента: {e}", exc_info=True)
            return None

    def delete_client(self, client_uuid: str) -> bool:
        self._ensure_login()
        try:
            inbound_ids = self._get_all_inbound_ids()
            deleted_any = False
            for iid in inbound_ids:
                try:
                    obj = self._get_inbound_raw(iid)
                    clients = obj.get('settings', {}).get('clients', [])
                    before = len(clients)
                    clients[:] = [c for c in clients if c.get('id') != client_uuid]
                    if len(clients) < before:
                        self._update_inbound(obj, iid)
                        deleted_any = True
                        logger.info(f"✅ Клиент удалён из inbound {iid}: {client_uuid[:8]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка удаления из inbound {iid}: {e}")
            if not deleted_any:
                logger.warning(f"Клиент {client_uuid[:8]}... не найден ни в одном inbound")
                return False
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления клиента: {e}", exc_info=True)
            return False

    def enable_client(self, client_uuid: str) -> bool:
        self._ensure_login()
        try:
            inbound_ids = self._get_all_inbound_ids()
            updated_any = False
            for iid in inbound_ids:
                try:
                    obj = self._get_inbound_raw(iid)
                    for c in obj.get('settings', {}).get('clients', []):
                        if c.get('id') == client_uuid:
                            c['enable'] = True
                            self._update_inbound(obj, iid)
                            updated_any = True
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка enable inbound {iid}: {e}")
            return updated_any
        except Exception as e:
            logger.error(f"❌ enable_client error: {e}", exc_info=True)
            return False

    def disable_client(self, client_uuid: str) -> bool:
        self._ensure_login()
        try:
            inbound_ids = self._get_all_inbound_ids()
            updated_any = False
            for iid in inbound_ids:
                try:
                    obj = self._get_inbound_raw(iid)
                    for c in obj.get('settings', {}).get('clients', []):
                        if c.get('id') == client_uuid:
                            c['enable'] = False
                            self._update_inbound(obj, iid)
                            updated_any = True
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка disable inbound {iid}: {e}")
            return updated_any
        except Exception as e:
            logger.error(f"❌ disable_client error: {e}", exc_info=True)
            return False

    def update_client_expiry(self, client_uuid: str, expiry_days: int) -> bool:
        self._ensure_login()
        try:
            inbound_ids = self._get_all_inbound_ids()
            updated_any = False
            for iid in inbound_ids:
                try:
                    obj = self._get_inbound_raw(iid)
                    for c in obj.get('settings', {}).get('clients', []):
                        if c.get('id') == client_uuid:
                            c['expiryTime'] = int((time.time() + expiry_days * 86400) * 1000)
                            self._update_inbound(obj, iid)
                            updated_any = True
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка update_expiry inbound {iid}: {e}")
            return updated_any
        except Exception as e:
            logger.error(f"❌ update_client_expiry error: {e}", exc_info=True)
            return False

    # ============== Auto-config reading ==============

    def _load_inbound_config(self):
        """Загрузить и закэшировать inbound-настройки для генерации ссылок"""
        if self._inbound_cache is not None:
            return self._inbound_cache
        try:
            obj = self._get_inbound_raw()
            ss = obj.get('streamSettings', {})
            rs = ss.get('realitySettings', {})

            port = obj.get('port', 443)
            server_names = rs.get('serverNames', [])
            sni = server_names[0] if server_names else 'www.google.com'
            short_ids = rs.get('shortIds', [])
            sid = short_ids[0] if short_ids else XUI_SHORT_ID
            # publicKey может быть напрямую в rs или внутри rs.settings
            pbk = (rs.get('settings', {}) or {}).get('publicKey', '') or rs.get('publicKey', '') or XUI_PUBLIC_KEY

            self._inbound_cache = {
                'port': port,
                'sni': sni,
                'pbk': pbk,
                'sid': sid,
                'server_ip': XUI_SERVER_IP,
            }
            logger.info(f"Inbound config loaded: port={port}, sni={sni}, pbk_set={bool(pbk)}, sid={sid[:8] if sid else 'none'}")
        except Exception as e:
            logger.error(f"Ошибка загрузки inbound config: {e}")
            self._inbound_cache = {
                'port': 443,
                'sni': 'www.google.com',
                'pbk': XUI_PUBLIC_KEY,
                'sid': XUI_SHORT_ID,
                'server_ip': XUI_SERVER_IP,
            }
        return self._inbound_cache

    # ============== Links ==============

    def get_vless_link(self, client_uuid: str, remark: str = "") -> str:
        cfg = self._load_inbound_config()
        sni = cfg['sni']
        port = cfg['port']
        pbk = cfg['pbk']
        sid = cfg['sid']
        rmk = quote(XUI_REMARK or remark or "VPN", safe='')
        return (
            f"vless://{client_uuid}@{cfg['server_ip']}:{port}?"
            f"security=reality&encryption=none&flow=xtls-rprx-vision"
            f"&sni={sni}&fp=chrome&pbk={pbk}"
            f"&sid={sid}&type=tcp#{rmk}"
        )

    def get_subscription_url(self, email: str) -> str:
        if XUI_SUB_URL:
            return f"{XUI_SUB_URL.rstrip('/')}/{email}"
        return f"http://{XUI_SERVER_IP}:2096/sub/{email}"
