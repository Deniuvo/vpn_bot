"""
Модуль для работы с API ЮMoney
Автоматическая проверка платежей
Поддерживает как прямое использование токена, так и библиотеку yoomoney
"""
import requests
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Пробуем импортировать библиотеку yoomoney (если установлена)
try:
    from yoomoney import Client as YMClient
    YOOMONEY_LIB_AVAILABLE = True
except ImportError:
    YOOMONEY_LIB_AVAILABLE = False
    logger.warning("Библиотека yoomoney не установлена. Используется прямое API.")


class YooMoneyAPI:
    """
    Класс для работы с API ЮMoney
    Использует API для проверки входящих платежей
    Поддерживает два режима: через библиотеку yoomoney и прямое API
    """
    
    def __init__(self, access_token: str, use_library: bool = True):
        """
        Инициализация API ЮMoney
        
        Args:
            access_token: Токен доступа к API ЮMoney
            use_library: Использовать библиотеку yoomoney (если доступна)
        """
        self.access_token = access_token
        self.use_library = use_library and YOOMONEY_LIB_AVAILABLE
        
        if self.use_library:
            self.client = YMClient(self.access_token)
            logger.info("Используется библиотека yoomoney для работы с API")
        else:
            self.base_url = "https://yoomoney.ru/api"
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            logger.info("Используется прямое API ЮMoney")
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Получить информацию об аккаунте
        
        Returns:
            Словарь с информацией об аккаунте или None при ошибке
        """
        try:
            response = self.session.post(f"{self.base_url}/account-info")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения информации об аккаунте: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Исключение при получении информации об аккаунте: {e}")
            return None
    
    def get_operation_history(self, 
                             records: int = 10,
                             label: Optional[str] = None,
                             from_date: Optional[datetime] = None,
                             till_date: Optional[datetime] = None) -> Optional[List[Dict]]:
        """
        Получить историю операций
        
        Args:
            records: Количество записей (максимум 100)
            label: Метка для фильтрации операций
            from_date: Начальная дата поиска
            till_date: Конечная дата поиска
        
        Returns:
            Список операций или None при ошибке
        """
        try:
            if self.use_library:
                # Используем библиотеку yoomoney
                kwargs = {"records": min(records, 100)}
                if label is not None:
                    kwargs["label"] = label
                history = self.client.operation_history(**kwargs)
                
                operations = []
                for op_raw in history.operations:
                    try:
                        if isinstance(op_raw, dict):
                            op_dict = {
                                'operation_id': op_raw.get('operation_id'),
                                'status': op_raw.get('status'),
                                'amount': float(op_raw.get('amount') or 0),
                                'direction': op_raw.get('direction'),
                                'label': op_raw.get('label'),
                                'datetime': op_raw.get('datetime'),
                                'message': op_raw.get('message'),
                                'details': op_raw.get('details'),
                                'comment': op_raw.get('comment'),
                                'title': op_raw.get('title'),
                            }
                        else:
                            op_dict = {
                                'operation_id': getattr(op_raw, 'operation_id', None),
                                'status': getattr(op_raw, 'status', None),
                                'amount': float(getattr(op_raw, 'amount', 0) or 0),
                                'direction': getattr(op_raw, 'direction', None),
                                'label': getattr(op_raw, 'label', None),
                                'datetime': getattr(op_raw, 'datetime', None),
                                'message': getattr(op_raw, 'message', None),
                                'details': getattr(op_raw, 'details', None),
                                'comment': getattr(op_raw, 'comment', None),
                                'title': getattr(op_raw, 'title', None),
                            }
                        operations.append(op_dict)
                    except Exception as op_err:
                        logger.warning(f"Пропускаем операцию из-за ошибки: {op_err}")
                        continue
                
                return operations
            else:
                # Прямое API
                params = {
                    "records": min(records, 100)
                }
                
                if label:
                    params["label"] = label
                
                if from_date:
                    params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                
                if till_date:
                    params["till"] = till_date.strftime("%Y-%m-%dT%H:%M:%S")
                
                response = self.session.post(f"{self.base_url}/operation-history", data=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'operations' in data:
                        return data['operations']
                    return []
                else:
                    logger.error(f"Ошибка получения истории операций: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Исключение при получении истории операций: {e}")
            return None
    
    def check_payment_by_amount_and_comment(self,
                                            amount: float,
                                            comment: str,
                                            hours_back: int = 24,
                                            commission_rate: float = 0.03) -> Optional[Dict]:
        """
        Проверить наличие платежа по сумме и комментарию
        Учитывает комиссию ЮMoney (обычно 3%)
        
        Args:
            amount: Сумма платежа (уже с учетом комиссии, т.е. то что пришло на кошелек)
            comment: Комментарий к платежу (метка/label или текст комментария)
            hours_back: За сколько часов назад искать платежи
            commission_rate: Процент комиссии (по умолчанию 3%)
        
        Returns:
            Операция платежа если найдена, иначе None
        """
        try:
            # Ищем платежи за последние N часов
            from_date = datetime.now() - timedelta(hours=hours_back)
            
            logger.info(f"Проверка платежа: сумма на кошельке={amount}₽, комментарий={comment}, часов назад={hours_back}")
            
            # Пробуем искать по label (метке)
            operations_by_label = self.get_operation_history(
                records=100,
                label=comment,
                from_date=from_date
            )
            
            # Также получаем все последние операции для поиска по комментарию в тексте
            all_operations = self.get_operation_history(
                records=100,
                from_date=from_date
            )
            
            # Объединяем результаты
            all_ops = operations_by_label or []
            if all_operations:
                # Добавляем операции, которых нет в списке по label
                label_op_ids = {op.get('operation_id') for op in all_ops}
                for op in all_operations:
                    if op.get('operation_id') not in label_op_ids:
                        all_ops.append(op)
            
            if not all_ops:
                logger.warning(f"Платежи не найдены за последние {hours_back} часов")
                return None
            
            logger.info(f"Найдено {len(all_ops)} операций за последние {hours_back} часов")
            
            # Диапазон сумм с учетом возможной погрешности комиссии (от 2% до 4%)
            min_amount = amount * 0.96  # Минимум (комиссия могла быть чуть больше)
            max_amount = amount * 1.04  # Максимум (комиссия могла быть чуть меньше или округление)
            
            # Ищем операцию с нужной суммой и комментарием
            for operation in all_ops:
                op_amount = float(operation.get('amount') or 0)
                op_status = (operation.get('status') or '').lower()
                op_direction = (operation.get('direction') or '').lower()
                op_label = operation.get('label') or ''
                op_message = operation.get('message') or ''
                op_details = operation.get('details') or ''
                op_comment = operation.get('comment') or ''
                
                # Проверяем сумму в диапазоне (с учетом возможных вариаций комиссии)
                amount_match = min_amount <= op_amount <= max_amount
                
                # Проверяем комментарий в разных полях (label, message, details, comment)
                comment_match = (
                    comment in str(op_label) or
                    comment in str(op_message) or
                    comment in str(op_details) or
                    comment in str(op_comment)
                )
                
                logger.debug(f"Операция {operation.get('operation_id')}: сумма={op_amount}₽, статус={op_status}, "
                           f"направление={op_direction}, label={op_label}, amount_match={amount_match}, comment_match={comment_match}")
                
                # Проверяем статус, направление и совпадение суммы и комментария
                if (amount_match and 
                    op_status == 'success' and 
                    op_direction == 'in' and
                    comment_match):
                    logger.info(f"✅ Платеж найден! Операция ID: {operation.get('operation_id')}, получено={op_amount}₽")
                    return operation
            
            logger.warning(f"Платеж не найден: ожидаемая сумма={amount}₽ (диапазон {min_amount:.2f}-{max_amount:.2f}₽), комментарий={comment}")
            logger.info(f"Последние операции: {[(op.get('amount'), op.get('label'), op.get('message')) for op in all_ops[:5]]}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка проверки платежа: {e}", exc_info=True)
            return None
    
    def check_payment_by_operation_id(self, operation_id: str) -> Optional[Dict]:
        """
        Проверить платеж по ID операции
        
        Args:
            operation_id: ID операции
        
        Returns:
            Информация об операции или None
        """
        try:
            response = self.session.post(
                f"{self.base_url}/operation-details",
                data={"operation_id": operation_id}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения операции: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Исключение при получении операции: {e}")
            return None


def create_payment_comment(user_id: int, tariff_type: str) -> str:
    """
    Создать уникальный комментарий к платежу
    
    Args:
        user_id: ID пользователя Telegram
        tariff_type: Тип тарифа
    
    Returns:
        Комментарий для платежа
    """
    return f"VPN_{user_id}_{tariff_type}"


def parse_payment_comment(comment: str) -> Optional[Dict]:
    """
    Распарсить комментарий платежа и извлечь информацию
    
    Args:
        comment: Комментарий к платежу
    
    Returns:
        Словарь с user_id и tariff_type или None
    """
    try:
        if not comment.startswith("VPN_"):
            return None
        
        parts = comment.split("_")
        if len(parts) >= 3:
            return {
                "user_id": int(parts[1]),
                "tariff_type": "_".join(parts[2:])  # На случай если tariff_type содержит "_"
            }
        return None
    except Exception:
        return None


def create_payment_url(wallet: str, amount: float, comment: str = "", label: str = "") -> str:
    """
    Создать URL для перехода на страницу оплаты ЮMoney
    Открывает страницу с выбором способа оплаты (QR, карта, банк и т.д.)
    
    Args:
        wallet: Номер кошелька ЮMoney (4100XXXXXXXXXX)
        amount: Сумма платежа
        comment: Комментарий к платежу
        label: Метка платежа (используется для идентификации)
    
    Returns:
        URL для оплаты через ЮMoney
    """
    import urllib.parse
    
    # Формируем URL для быстрого платежа через форму ЮMoney
    # Используем формат БЕЗ параметра payment-type, чтобы показались все способы
    # Формат quickpay-form: "shop" или "donate" позволяет выбрать любой способ оплаты
    params = {
        "receiver": wallet,
        "quickpay-form": "shop",  # shop - стандартная форма с выбором всех способов
        "targets": comment if comment else "Оплата VPN подписки",
        "sum": str(amount)
        # ВАЖНО: Не указываем payment-type вообще!
        # Это позволит пользователю выбрать ЛЮБОЙ доступный способ оплаты
        # (СБП, Т-банк, QR-код, Сбер, ВТБ, карта, кошелек ЮMoney и т.д.)
    }
    
    # Добавляем метку, если указана (для идентификации платежа)
    if label:
        params["label"] = label
    
    # Кодируем параметры в URL
    query_string = urllib.parse.urlencode(params)
    
    # URL для оплаты через форму ЮMoney - откроется страница со ВСЕМИ способами оплаты
    payment_url = f"https://yoomoney.ru/quickpay/confirm.xml?{query_string}"
    
    return payment_url


def create_simple_payment_link(wallet: str, amount: float, comment: str = "") -> str:
    """
    Создать простую ссылку для перевода на кошелек ЮMoney
    Альтернативный вариант через форму быстрого платежа
    
    Args:
        wallet: Номер кошелька ЮMoney
        amount: Сумма платежа
        comment: Комментарий к платежу
    
    Returns:
        Ссылка для оплаты
    """
    import urllib.parse
    
    # Используем тот же формат, что и основная функция
    params = {
        "receiver": wallet,
        "quickpay-form": "donate",  # donate показывает все способы оплаты
        "targets": comment if comment else "Оплата VPN подписки",
        "sum": str(amount)
        # Не указываем payment-type, чтобы показались ВСЕ способы
    }
    
    query_string = urllib.parse.urlencode(params)
    payment_link = f"https://yoomoney.ru/quickpay/confirm.xml?{query_string}"
    
    return payment_link

