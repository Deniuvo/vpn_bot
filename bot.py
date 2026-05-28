"""
Главный файл Telegram бота для продажи VPN услуг
"""
import os
import sys
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from database import db
from xui_api import XUIManager
import config_server
import threading
from yoomoney_api import YooMoneyAPI, create_payment_comment, parse_payment_comment, create_payment_url, create_simple_payment_link
from cryptocloud_api import cryptocloud, create_cryptocloud_order_id
from io import BytesIO
from telegram import InputFile

# Конфигурация бота
BOT_TOKEN = "8955366761:AAHxJ_r6epX6a_qKvbScMXxdJ19I4K688kw"
BOT_NAME = "CloudHapp"
SUPPORT_USERNAME = "@deniuvo"
YMONEY_WALLET = "4100119393589473"
# Админская группа для рассылок (можно установить через переменную окружения)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", None)  # ID админской группы

# Комиссия ЮMoney (обычно 3% + 45 рублей минимум, но для быстрых платежей обычно 3%)
YOOMONEY_COMMISSION_RATE = float(os.getenv("YOOMONEY_COMMISSION_RATE", "0.03"))  # 3% комиссия

# API ЮMoney для автоматической проверки платежей
# OAuth2 credentials
# OAuth2 приложение «CloudHapp» в кабинете ЮMoney
YOOMONEY_CLIENT_ID = os.getenv(
    "YOOMONEY_CLIENT_ID",
    "9BC961BE2FCB3D6A07320B85144EE045C4C73618A78A617C27EC0894397DC61F",
)
YOOMONEY_CLIENT_SECRET = os.getenv(
    "YOOMONEY_CLIENT_SECRET",
    "14ECCC895A41D72C733363E6EC2FEC601C53957DACC007EB39A5B093D9500EDB905FEE99134673BA7076F1FCA75A0DA0F97E879112B72FDAA812EC188402869D",
)
YMONEY_ACCESS_TOKEN = os.getenv("YMONEY_ACCESS_TOKEN", None)  # Токен доступа к API (получается один раз через OAuth2)
USE_YOOMONEY_API = os.getenv("USE_YOOMONEY_API", "true").lower() == "true"  # Использовать API для проверки

# IP сервера - нужно будет настроить
SERVER_IP = os.getenv("SERVER_IP", os.getenv("XUI_SERVER_IP", "YOUR_SERVER_IP"))

# Тарифы
TARIFFS = {
    "trial": {"name": "Попробовать на 2 дня", "price": 0, "days": 2},  # 2 дня пробный период
    "1_month": {"name": "1 месяц", "price": 120, "days": 30},
    "3_months": {"name": "3 месяца", "price": 400, "days": 90},
    "1_year": {"name": "1 год", "price": 1200, "days": 365}
}

# Комиссия партнёрской программы: 20% с первого платного платежа реферала
REFERRAL_FIRST_PAYMENT_COMMISSION_RATE = float(
    os.getenv("REFERRAL_FIRST_PAYMENT_COMMISSION_RATE", "0.20")
)  # 20% с первого платного платежа приглашённого пользователя
REFERRAL_MIN_PAYOUT = float(os.getenv("REFERRAL_MIN_PAYOUT", "1000"))  # Минимальная сумма для вывода

# Состояния для ConversationHandler
WAITING_PAYMENT = 1  # Ожидание платежа (через API или скриншот)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Проверка наличия qrcode (может быть не установлен)
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    logger.warning("⚠️ Модуль qrcode не установлен! QR-коды не будут работать. Установите: pip install qrcode[pil]==7.4.2")

# Инициализация XUI менеджера
xui_manager = None


def get_back_button():
    """Возвращает кнопку "Назад" в главное меню"""
    return [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]]


def get_main_keyboard(include_referral: bool = True, user_id: int = None) -> InlineKeyboardMarkup:
    """Главное меню бота"""
    device_count = 0
    if user_id:
        try:
            device_count = db.count_user_devices(user_id)
        except Exception:
            pass
    device_text = f"📱 Устройства ({device_count}/3)" if device_count > 0 else "📱 Устройства"

    rows = [
        [InlineKeyboardButton("☁️ Подключить VPN", callback_data="buy_vpn")],
        [InlineKeyboardButton("📖 Инструкция", callback_data="instruction")],
        [
            InlineKeyboardButton("⚡ Статус", callback_data="check_status"),
            InlineKeyboardButton("📄 Мой конфиг", callback_data="my_config"),
        ],
        [
            InlineKeyboardButton(device_text, callback_data="my_devices"),
        ],
    ]
    if include_referral:
        rows.append([InlineKeyboardButton("💰 Партнёрская программа", callback_data="referral_program")])
    rows.extend([
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")],
        [InlineKeyboardButton("Конфиденциальность", callback_data="privacy")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="user_stats")],
    ])
    return InlineKeyboardMarkup(rows)


def get_welcome_text(first_name: str, referral_registered: bool = False) -> str:
    """Приветствие CloudHapp."""
    referral_block = ""
    if referral_registered:
        referral_block = (
            "\n🤝 Вы перешли по реферальной ссылке — с первой оплаты "
            "пригласивший получит *20 %* комиссии.\n"
        )
    return f"""☁️ *{BOT_NAME}*

Привет, {first_name}! 👋
{referral_block}
Быстрый и надёжный VPN для всех устройств.

*Что внутри:*
🔐 VLESS + Reality — не блокируется
⚡ Стабильная скорость
📱 iOS · Android · Windows · macOS · Linux

*Команды:*
☁️ /buy — подписка
📖 /instruction — подключение
⚡ /status — статус VPN
📄 /myconfig — конфиг
💬 /support — поддержка
/privacy — конфиденциальность
👥 /stats — пользователи
💰 /referral — партнёрка

Выберите действие 👇
"""


def get_connection_instructions() -> str:
    """Инструкция по подключению через Happ (после выдачи конфига)."""
    return """
*Подключение через Happ*

📱 *iOS / Android (QR — рекомендуется):*
1. Откройте Happ → «+» → «Отсканировать QR»
2. Наведите камеру на QR-код выше

📱 *iOS / Android (ссылка на подписку):*
1. Откройте Happ → «+» → «Добавить конфигурацию»
2. Выберите «Импорт из буфера обмена»
3. Скопируйте ссылку на подписку ниже и вернитесь в Happ

💻 *Windows / macOS / Linux:*
1. Скачайте Happ Desktop — https://www.happ.su
2. Вставьте ссылку на подписку → «Добавить конфигурацию»

*Скачать Happ:*
📱 iOS — https://apps.apple.com/app/happ-proxy-utility/id6504287215
📱 Android — https://play.google.com/store/apps/details?id=com.happproxy
💻 Desktop — https://www.happ.su

📄 /myconfig — конфиг снова
⚡ /status — статус VPN
💬 /support — поддержка
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, есть ли реферальный код в параметрах команды
    referral_code = None
    if update.message and update.message.text:
        parts = update.message.text.split()
        if len(parts) > 1:
            referral_code = parts[1]
    
    # Регистрируем реферала, если есть код и это не сам реферер
    referral_registered = False
    if referral_code:
        referrer_id = db.get_referrer_by_code(referral_code)
        if referrer_id and referrer_id != user.id:
            # Регистрируем реферала (функция проверит, не зарегистрирован ли уже)
            if db.register_referral(referrer_id, user.id, referral_code):
                referral_registered = True
                logger.info(f"Реферал зарегистрирован: referred_id={user.id}, referrer_id={referrer_id}, code={referral_code}")
    
    welcome_text = get_welcome_text(user.first_name, referral_registered=referral_registered)
    reply_markup = get_main_keyboard(include_referral=True, user_id=user.id)

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy"""
    user = update.effective_user
    logger.info(f"/buy called by user={user.id if user else 'unknown'}")
    await show_tariffs(update, context)
    return WAITING_PAYMENT


async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные тарифы"""
    user = update.effective_user
    logger.info(f"show_tariffs called by user={user.id if user else 'unknown'}")
    text = f"""
☁️ *Тарифы {BOT_NAME}*

🎁 *Пробный период — 2 дня* — бесплатно
   _Один раз на аккаунт_

📅 *1 месяц* — 120 ₽

⭐ *3 месяца* — 400 ₽

⭐ *1 год* — 1200 ₽

Выберите тариф 👇
"""

    keyboard = [
        [InlineKeyboardButton("🎁 Попробовать 2 дня — бесплатно", callback_data="tariff_trial")],
        [InlineKeyboardButton("☁️ 1 месяц — 120 ₽", callback_data="tariff_1_month")],
        [InlineKeyboardButton("⭐ 3 месяца — 400 ₽", callback_data="tariff_3_months")],
        [InlineKeyboardButton("⭐ 1 год — 1200 ₽", callback_data="tariff_1_year")],
    ] + get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def handle_tariff_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора тарифа"""
    query = update.callback_query
    await query.answer()

    tariff_type = query.data.replace("tariff_", "")
    tariff_info = TARIFFS.get(tariff_type)

    if not tariff_info:
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте снова или 💬 /support")
        return

    user = query.from_user
    
    # Для бесплатного trial тарифа - сразу выдаем конфиг без оплаты
    if tariff_type == "trial":
        # Проверяем, получал ли пользователь когда-либо trial (даже если истек)
        if db.user_has_ever_had_trial(user.id):
            await query.edit_message_text(
                "🎁 Извини, но пробный период можно получить только один раз!\n\n"
                "Вы уже использовали бесплатный пробный период. "
                "Выберите один из платных тарифов для продолжения."
            )
            return
        
        # Проверяем, есть ли у пользователя активная платная подписка
        is_active = db.check_user_active(user.id)
        if is_active:
            await query.edit_message_text(
                "✅ У вас уже есть активная подписка. Конфиг: /myconfig"
            )
            return
        
        # Генерируем конфиг сразу без оплаты
        try:
            await query.edit_message_text(
                "🎁 *Активирую пробный период...*\n\n"
                "Создаю подписку, подождите несколько секунд.",
                parse_mode='Markdown'
            )
            await process_payment_and_generate_config(update, context, user, tariff_type, is_callback=True)
        except Exception as e:
            logger.error(f"Ошибка при генерации trial конфига: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Не удалось создать подписку. Попробуйте позже или 💬 /support"
            )
        return ConversationHandler.END

    # Для платных тарифов - стандартный процесс оплаты
    # Сохраняем выбранный тариф в контексте
    context.user_data['selected_tariff'] = tariff_type
    
    # Генерируем уникальный комментарий для платежа
    payment_comment = create_payment_comment(user.id, tariff_type)
    context.user_data['payment_comment'] = payment_comment
    context.user_data['payment_amount'] = tariff_info['price']

    # Создаем ссылку на оплату через ЮMoney
    payment_url = create_payment_url(
        wallet=YMONEY_WALLET,
        amount=tariff_info['price'],
        comment=payment_comment,
        label=payment_comment
    )
    
    # Также создаем простую ссылку для перевода
    simple_payment_link = create_simple_payment_link(
        wallet=YMONEY_WALLET,
        amount=tariff_info['price'],
        comment=payment_comment
    )

    # Формируем текст оплаты с кнопкой для перехода на оплату
    payment_text = f"""
💳 *Оплата — {BOT_NAME}*

☁️ *Тариф:* {tariff_info['name']}
💰 *Сумма:* {tariff_info['price']} ₽

*Как оплатить:*
1. Нажмите *«Оплатить картой РФ / ЮMoney / СберPay»*
2. Выберите способ: карта, QR, Т-Банк, Сбер или другой банк
3. Вернитесь сюда → *«Проверить оплату»*

✅ Оплата проверяется автоматически, конфиг придёт сюда.
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить картой РФ / ЮMoney / СберPay", url=payment_url)],
        [InlineKeyboardButton("🪙 Оплата криптовалютой / TON / USDT", callback_data="pay_crypto")],
        [InlineKeyboardButton("✅ Проверить оплату", callback_data="check_payment")],
    ] + get_back_button()

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        payment_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    # Переходим в состояние ожидания платежа
    return WAITING_PAYMENT


async def check_payment_with_api(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Проверить оплату через API ЮMoney
    
    Returns:
        True если оплата найдена и подтверждена
    """
    if not USE_YOOMONEY_API or not YMONEY_ACCESS_TOKEN:
        return False
    
    try:
        user = update.effective_user
        tariff_type = context.user_data.get('selected_tariff')
        payment_comment = context.user_data.get('payment_comment')
        payment_amount = context.user_data.get('payment_amount')
        
        logger.info(f"Проверка платежа для user_id={user.id}, тариф={tariff_type}, сумма={payment_amount}, комментарий={payment_comment}")
        
        if not all([tariff_type, payment_comment, payment_amount]):
            logger.warning(f"Недостаточно данных для проверки: tariff={tariff_type}, comment={payment_comment}, amount={payment_amount}")
            return False
        
        if not USE_YOOMONEY_API or not YMONEY_ACCESS_TOKEN:
            logger.warning("API ЮMoney отключен или токен не установлен")
            return False
        
        yoomoney = YooMoneyAPI(YMONEY_ACCESS_TOKEN, use_library=False)
        
        # Рассчитываем сумму с учетом комиссии ЮMoney (обычно ~3%)
        # Диапазон ±4% покрывает вариации комиссии и округления
        amount_with_commission = payment_amount * (1 - YOOMONEY_COMMISSION_RATE)
        
        logger.info(f"Ищу платеж: ожидаемая сумма на кошельке={amount_with_commission:.2f}₽ (с учетом комиссии {YOOMONEY_COMMISSION_RATE*100}%)")
        logger.info(f"Ожидаемый комментарий: {payment_comment}")
        
        # Проверяем платеж
        operation = yoomoney.check_payment_by_amount_and_comment(
            amount=amount_with_commission,
            comment=payment_comment,
            hours_back=24
        )
        
        if operation:
            operation_id = operation.get('operation_id', 'unknown')
            received_amount = operation.get('amount', 0)
            logger.info(f"✅ Платеж подтвержден для user_id={user.id}, operation_id={operation_id}, получено={received_amount}₽ (платил {payment_amount}₽)")
            return True
        else:
            logger.warning(f"❌ Платеж не найден для user_id={user.id}, сумма={payment_amount}₽ (ожидаем {amount_with_commission:.2f}₽ на кошельке), комментарий={payment_comment}")
            # Пробуем найти платеж только по сумме с учетом комиссии (если комментарий не совпал)
            min_amount = amount_with_commission * 0.96
            max_amount = amount_with_commission * 1.04
            logger.info(f"Попытка найти платеж только по сумме с учетом комиссии (за последние 24 часа)...")
            from datetime import timedelta
            recent_ops = yoomoney.get_operation_history(
                records=100,
                from_date=datetime.now() - timedelta(hours=24)
            )
            if recent_ops:
                logger.info(f"Проверяю {len(recent_ops)} операций за последние 24 часа...")
                # Ищем платежи в диапазоне суммы с учетом комиссии
                matching_amount_ops = [op for op in recent_ops 
                                      if min_amount <= float(op.get('amount') or 0) <= max_amount
                                      and (op.get('status') or '').lower() == 'success'
                                      and (op.get('direction') or '').lower() == 'in']
                if matching_amount_ops:
                    logger.info(f"⚠️ Найдены платежи с подходящей суммой ({[op.get('amount') for op in matching_amount_ops[:3]]}₽), но без совпадения комментария")
                    logger.info(f"⚠️ Комментарии в найденных платежах: {[str(op.get('label') or op.get('message') or op.get('comment') or '') for op in matching_amount_ops[:3]]}")
                    # Если нашли платеж(и) только по сумме - принимаем самый свежий
                    # Сортируем по дате (самый свежий первый) и берем первый
                    matching_amount_ops.sort(key=lambda x: x.get('datetime', ''), reverse=True)
                    op = matching_amount_ops[0]
                    logger.warning(f"⚠️ Принимаем платеж только по сумме (комментарий не совпал): operation_id={op.get('operation_id')}, получено={op.get('amount')}₽, дата={op.get('datetime', 'unknown')}")
                    return True
                else:
                    logger.warning(f"⚠️ Платежи с суммой в диапазоне {min_amount:.2f}₽ - {max_amount:.2f}₽ не найдены")
                    # Логируем все найденные суммы для отладки
                    all_amounts = [float(op.get('amount') or 0) for op in recent_ops if (op.get('direction') or '').lower() == 'in' and (op.get('status') or '').lower() == 'success']
                    if all_amounts:
                        logger.info(f"Найденные суммы входящих платежей за 24 часа: {sorted(set(all_amounts), reverse=True)[:10]}")
            else:
                logger.warning(f"⚠️ Не удалось получить операции за последние 24 часа")
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка проверки платежа через API: {e}", exc_info=True)
        return False


async def handle_check_payment_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки 'Проверить оплату'"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    tariff_type = context.user_data.get('selected_tariff')
    
    if not tariff_type:
        await query.edit_message_text("❌ Ошибка сессии. Начните заново: /buy")
        return ConversationHandler.END
    
    # Проверяем активную подписку
    existing_user = db.get_user(user.id)
    if existing_user and db.check_user_active(user.id):
        await query.edit_message_text(
            "✅ У вас уже есть активная подписка. Конфиг: /myconfig"
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text("🔍 Проверяю оплату...")
    
    # Проверяем оплату через API
    payment_confirmed = await check_payment_with_api(update, context)
    
    if payment_confirmed:
        try:
            # Используем специальный объект для callback query
            class CallbackUpdate:
                def __init__(self, callback_query):
                    self.callback_query = callback_query
            
            callback_update = CallbackUpdate(query)
            await process_payment_and_generate_config(callback_update, context, user, tariff_type, is_callback=True)
            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка при генерации конфига для user_id={user.id}, tariff={tariff_type}: {e}", exc_info=True)
            error_message = str(e)
            await query.edit_message_text(
                f"❌ Не удалось создать конфиг.\n\n"
                f"Ошибка: {error_message}\n\n"
                f"💬 Поддержка: /support"
            )
            return ConversationHandler.END
    else:
        await query.edit_message_text(
            "⏳ Оплата пока не найдена.\n\n"
            "Возможные причины:\n"
            "• Платёж ещё не поступил (1–2 мин)\n"
            "• Неверный комментарий\n"
            "• Неверная сумма\n\n"
            "Попробуйте снова через минуту 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_payment")]
            ] + get_back_button())
        )
        return WAITING_PAYMENT


async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка скриншота оплаты (резервный метод)"""
    user = update.effective_user
    tariff_type = context.user_data.get('selected_tariff')

    if not tariff_type:
        await update.message.reply_text(
            "Ошибка сессии. Начните покупку заново: /buy"
        )
        return ConversationHandler.END

    # Проверяем, есть ли уже активная подписка
    existing_user = db.get_user(user.id)
    if existing_user and db.check_user_active(user.id):
        await update.message.reply_text(
            "✅ У вас уже есть активная подписка. Конфиг: /myconfig"
        )
        context.user_data.clear()
        return ConversationHandler.END

    # Если включен API, сначала пробуем проверить через API
    if USE_YOOMONEY_API and YMONEY_ACCESS_TOKEN:
        payment_confirmed = await check_payment_with_api(update, context)
        if payment_confirmed:
            try:
                await process_payment_and_generate_config(update, context, user, tariff_type)
                context.user_data.clear()
                return ConversationHandler.END
            except Exception as e:
                logger.error(f"Ошибка при генерации конфига: {e}")
    
    # Получаем скриншот
    photo = update.message.photo
    
    # Если пользователь отправил текст вместо фото, напоминаем
    if update.message.text and not photo:
        if USE_YOOMONEY_API and YMONEY_ACCESS_TOKEN:
            await update.message.reply_text(
                "✅ Используйте кнопку *«Проверить оплату»*.\n\n"
                "⏳ Если оплата не видна — подождите 1–2 мин и повторите.\n"
                "💬 Проблема осталась — /support",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "📷 Отправьте *скриншот чека* (фото), а не текст.\n\n"
                "💬 Проблемы с оплатой — /support",
                parse_mode='Markdown'
            )
        return WAITING_PAYMENT
    
    if not photo:
        # Если API включен, не просим скриншот
        if USE_YOOMONEY_API and YMONEY_ACCESS_TOKEN:
            await update.message.reply_text(
                "✅ Кнопка *«Проверить оплату»*.\n"
                "📷 Или скриншот чека (фото) для ручной проверки.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "📷 Отправьте скриншот чека об оплате (фото)."
            )
        return WAITING_PAYMENT

    # Получаем файл фотографии (для логирования или ручной проверки)
    file = await context.bot.get_file(photo[-1].file_id)

    # Отправляем уведомление о проверке
    await update.message.reply_text(
        "🔍 Проверяю оплату, подождите..."
    )

    # Генерируем конфиг (ручная проверка или автоматическая для демо)
    try:
        await process_payment_and_generate_config(update, context, user, tariff_type)
    except Exception as e:
        logger.error(f"Ошибка при генерации конфига: {e}")
        await update.message.reply_text(
            "❌ Не удалось создать подписку. 💬 /support"
        )
        return ConversationHandler.END

    context.user_data.clear()
    return ConversationHandler.END


async def process_payment_and_generate_config(update, context: ContextTypes.DEFAULT_TYPE,
                                             user, tariff_type: str, is_callback: bool = False):
    """Обработка оплаты и генерация конфига
    
    Args:
        update: Update или CallbackQuery объект
        context: Context
        user: Пользователь
        tariff_type: Тип тарифа
        is_callback: True если вызвано из callback query
    """
    # Создаём клиента в 3X-UI
    logger.info(f"Создаю VLESS клиента для user_id={user.id}...")
    
    tariff_info = TARIFFS[tariff_type]
    expiry_days = tariff_info['days']
    
    try:
        # Удаляем старого клиента, если существует
        existing_user = db.get_user(user.id)
        if existing_user and existing_user.get('xray_uuid'):
            old_uuid = existing_user['xray_uuid']
            logger.info(f"Удаляю старого клиента {old_uuid[:8]}... для user_id={user.id}")
            xui_manager.delete_client(old_uuid)
        
        # Создаём нового клиента
        xui_email = f"vpn_{user.id}"
        client_data = xui_manager.create_client(
            user_id=user.id,
            email=xui_email,
            expiry_days=expiry_days,
            remark="CloudHapp"
        )
        
        if not client_data:
            raise Exception("Не удалось создать клиента в 3X-UI")
        
        client_uuid = client_data['uuid']
        logger.info(f"✅ VLESS клиент создан: uuid={client_uuid[:8]}...")
        
        # Генерируем vless:// ссылку и URL подписки
        vless_link = xui_manager.get_vless_link(client_uuid, remark=f"CloudHapp-{user.id}")
        sub_url = xui_manager.get_subscription_url(xui_email)
        logger.info(f"✅ VLESS ссылка сгенерирована для user_id={user.id}")
        logger.info(f"✅ URL подписки: {sub_url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания VLESS клиента: {e}", exc_info=True)
        raise Exception("Не удалось создать подписку. Свяжитесь с администратором.")

    # Сохраняем в базу данных
    if existing_user:
        success = db.update_user_subscription(
            user_id=user.id,
            username=user.username or "unknown",
            subscription_type=tariff_type,
            xray_uuid=client_uuid,
            xray_email=xui_email,
            vless_link=vless_link
        )
    else:
        success = db.add_user(
            user_id=user.id,
            username=user.username or "unknown",
            subscription_type=tariff_type,
            xray_uuid=client_uuid,
            xray_email=xui_email,
            vless_link=vless_link
        )

    if not success:
        raise Exception("Не удалось сохранить пользователя в базу данных")
    
    # Начисляем комиссию рефереру, если это реферал и это платная покупка
    if tariff_type != "trial":
        purchase_amount = TARIFFS[tariff_type]['price']
        commission_amount = purchase_amount * REFERRAL_FIRST_PAYMENT_COMMISSION_RATE
        
        if db.update_referral_purchase(user.id, purchase_amount, commission_amount):
            # Находим реферера для уведомления
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT referrer_id FROM referrals 
                WHERE referred_id = ? AND purchased_at IS NOT NULL
                ORDER BY id DESC LIMIT 1
            """, (user.id,))
            referrer_result = cursor.fetchone()
            conn.close()
            
            if referrer_result:
                referrer_id = referrer_result[0]
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 *Отличные новости!*\n\n"
                             f"Твой реферал совершил покупку!\n\n"
                             f"💰 Начислено комиссии: *{commission_amount:.2f} ₽*\n\n"
                             f"Статистика и выплаты: /referral",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Комиссия начислена: referrer_id={referrer_id}, amount={commission_amount:.2f}₽")
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления рефереру: {e}")

    # Получаем данные пользователя для отображения expiry_date
    user_data_after = db.get_user(user.id)
    expiry_date = datetime.fromisoformat(user_data_after['expiry_date']).strftime("%d.%m.%Y")

    success_text = f"""
✅ *Подписка активирована — {BOT_NAME}*

☁️ Конфиг готов!

*Тариф:* {tariff_info['name']}
📅 *Действует до:* {expiry_date}

Сейчас отправлю ссылку-подписку и QR-код для подключения через *Happ* 👇
"""

    # Отправляем текстовое сообщение
    chat_id = user.id
    if is_callback:
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.from_user.id
    
    if is_callback:
        await context.bot.send_message(
            chat_id=chat_id,
            text=success_text,
            parse_mode='Markdown'
        )
    else:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                success_text,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=success_text,
                parse_mode='Markdown'
            )

    # 1. QR-код subscription URL (для Happ — с метаданными и автообновлением)
    if QRCODE_AVAILABLE and sub_url:
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(sub_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(img_byte_arr, filename="config_qr.png"),
                caption="📱 *QR-код подписки для Happ*\n\nHapp → «+» → «Отсканировать QR» → наведите камеру\n\n_Будет показан заголовок, трафик и срок подписки_",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка генерации QR-кода: {e}")
    else:
        logger.warning("QR-код не отправлен: модуль qrcode не установлен или нет subscription URL")

    # 2. Инструкции по подключению
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_connection_instructions(),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка отправки инструкций: {e}")

    # 3. Subscription URL текстом
    if sub_url:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📋 *Ссылка-подписка (для Happ — с метаданными):*\n\n`{sub_url}`\n\n_Скопируйте → Happ → «+» → «Добавить подписку по URL»_",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки subscription URL: {e}")

    # Отправляем уведомление поддержке (если нужно)
    # admin_chat_id = YOUR_ADMIN_CHAT_ID
    # await context.bot.send_message(
    #     chat_id=admin_chat_id,
    #     text=f"Новая покупка:\nПользователь: @{user.username or 'unknown'} ({user.id})\nТариф: {tariff_info['name']}"
    # )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    status_text = f"⚡ *Статус {BOT_NAME}*\n\n🔍 Проверяю сервер...\n\n"

    try:
        # Проверяем доступность 3X-UI панели
        xui_manager._ensure_login()
        status_text += "✅ VPN-сервер доступен.\n"
        status_text += f"IP: `{SERVER_IP}`\n"
        status_text += "Протокол: VLESS+Reality (Xray)\n"
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        status_text += "⚠️ VPN временно недоступен.\n"
        status_text += "💬 Попробуйте позже или /support\n"

    status_text += f"\n💬 Поддержка: {SUPPORT_USERNAME}"

    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def instruction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /instruction - инструкция по подключению VPN"""
    instruction_text = f"""
📖 *Инструкция — {BOT_NAME}*

*Что это* 🔐
VLESS + Reality — современный VPN-протокол, который маскируется под обычный HTTPS-трафик и практически не блокируется.

*Преимущества:*
• 🚀 Не определяется DPI
• ⚡ Высокая скорость
• 🔐 Надёжное шифрование
• 📱 iOS · Android · Windows · macOS · Linux

*Шаг 1.* Установите приложение *Happ*:
📱 iOS — https://apps.apple.com/app/happ-proxy-utility/id6504287215
📱 Android — https://play.google.com/store/apps/details?id=com.happproxy
💻 Desktop — https://www.happ.su

*Шаг 2.* Оформите подписку: /buy — после оплаты придёт ссылка и QR-код

*Шаг 3.* Подключитесь:
📱 *Через QR:* Happ → «+» → «Отсканировать QR» → наведите камеру
🔗 *Через ссылку:* скопируйте `vless://...` → Happ → «+» → «Импорт из буфера»

*Шаг 4.* Нажмите кнопку подключения в Happ ✅

☁️ Пробный период и тарифы: /buy
"""

    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            instruction_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            instruction_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /support"""
    support_text = f"""
💬 *Поддержка — {BOT_NAME}*

Telegram: {SUPPORT_USERNAME}
🕐 Круглосуточно

*Частые вопросы:*

 *Конфиг* → /myconfig
⚡ *VPN не работает* → /status, затем /support
📅 *Срок подписки* → дата в /myconfig
"""

    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            support_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            support_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - статистика активных пользователей"""
    # Получаем статистику
    stats = db.get_active_users_stats()
    
    # Формируем текст со статистикой
    stats_text = f"""
👥 *Пользователи {BOT_NAME}*

✅ *Активных:* {stats['total_active']}
👥 *Всего:* {stats['total_users']}

*По тарифам:*
"""
    
    # Статистика по каждому тарифу
    for tariff_key, tariff_info in TARIFFS.items():
        count = stats['by_tariff'].get(tariff_key, 0)
        if tariff_key == 'trial':
            stats_text += f"\n• *☁️ {tariff_info['name']}* - {count} чел."
        else:
            stats_text += f"\n• *{tariff_info['name']}* - {count} чел."
    
    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /privacy - политика конфиденциальности"""
    privacy_text = """
*Политика конфиденциальности*

Мы не собираем и не можем видеть содержимое вашего трафика. Все соединения защищены end-to-end шифрованием VLESS+Reality.

*Что мы НЕ видим:*
- Содержимое запросов и посещаемые сайты
- Пароли, сообщения, файлы
- Историю браузера

Администратор бота технически не может расшифровать ваши данные. Для защиты используются TLS 1.3, X25519, Reality и BLAKE2s. Сервер видит только зашифрованные пакеты, а ваш приватный ключ хранится исключительно на вашем устройстве.

*Технические данные, которые мы видим:*
- Внутренний IP-адрес в VPN-сети
- Время подключения и отключения
- Объем переданного трафика (без содержимого)

Эти данные необходимы для работы сервиса, управления подписками и защиты от злоупотреблений.

*Защита от третьих лиц*
Ваш трафик защищен от провайдеров, публичных Wi-Fi и перехвата в открытых сетях.

*Хранение данных*
- Конфигурационные файлы хранятся на сервере для выдачи по запросу
- Приватные ключи генерируются при создании конфига, но не позволяют расшифровать трафик
- Ваш приватный ключ находится только в конфиге на вашем устройстве

*Что мы НЕ делаем*
- Не логируем содержимое запросов
- Не отслеживаем посещаемые сайты
- Не передаем данные третьим лицам
- Не используем данные для рекламы

*Прозрачность*
Мы открыто заявляем, какие технические данные нужны для работы сервиса. По вопросам обращайтесь в поддержку: /support

*Итог*
Ваш трафик защищен современным шифрованием. Администратор не имеет доступа к содержимому ваших данных — это технически невозможно благодаря архитектуре протокола.
"""

    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            privacy_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            privacy_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /referral - партнерская программа"""
    user = update.effective_user
    
    # Получаем или создаем реферальный код
    referral_code = db.get_referral_code(user.id)
    if not referral_code:
        referral_code = db.create_referral_code(user.id)
    
    # Получаем статистику
    stats = db.get_referral_stats(user.id)
    
    # Формируем реферальную ссылку
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    referral_text = f"""
💰 *Партнёрская программа — {BOT_NAME}*

*Как это работает:*
1. Делись реферальной ссылкой с друзьями
2. Друг переходит по ссылке и покупает VPN
3. С *первого платного* платежа — *20 %* тебе

*🔗 Твоя ссылка:*
`{referral_link}`

*Статистика:*
👥 Рефералов: *{stats['total_referrals']}*
☁️ Купили: *{stats['total_purchases']}*
💰 Заработок: *{stats['total_earnings']} ₽*
💵 К выводу: *{stats['available_earnings']} ₽*
📤 Запрошено: *{stats['requested_earnings']} ₽*
✅ Выплачено: *{stats['paid_earnings']} ₽*

*Пример (первый платёж):*
• 1 месяц (120 ₽) → *24 ₽*
• 3 месяца (400 ₽) → *80 ₽*
• 1 год (1200 ₽) → *240 ₽*

Комиссия — один раз с первой оплаты приглашённого.

*Как делиться:*
1. Нажми «📋 Скопировать ссылку»
2. Отправь друзьям в Telegram или соцсетях
3. Получай комиссию с каждого нового клиента
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Скопировать ссылку", callback_data=f"referral_copy_{referral_code}")],
        [InlineKeyboardButton("📊 Подробная статистика", callback_data="referral_stats")],
        [InlineKeyboardButton("💸 Запросить выплату", callback_data="referral_request_payout")]
    ] + get_back_button()
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            referral_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            referral_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def resettrial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить trial подписку (одноразовая команда для тестирования)"""
    user = update.effective_user

    if not db.user_has_ever_had_trial(user.id):
        await update.message.reply_text(
            "✅ У вас нет использованного пробного периода. Можете активировать: /start"
        )
        return

    success = db.delete_user(user.id)
    if success:
        await update.message.reply_text(
            "✅ Пробный период сброшен. Нажмите /start, чтобы получить его заново."
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось сбросить. Попробуйте позже или напишите /support"
        )


async def handle_referral_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать подробную статистику партнерской программы"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    stats = db.get_referral_stats(user.id)
    
    stats_text = f"""
*📊 Подробная статистика партнерской программы*

*👥 Рефералы:*
• Всего перешло по твоей ссылке: *{stats['total_referrals']}*
• Совершили покупку: *{stats['total_purchases']}*
• Конверсия: *{(stats['total_purchases'] / stats['total_referrals'] * 100) if stats['total_referrals'] > 0 else 0:.1f}%*

*💰 Финансы:*
• Общий заработок: *{stats['total_earnings']} ₽*
• Доступно для вывода: *{stats['available_earnings']} ₽*
• Запрошено на выплату: *{stats['requested_earnings']} ₽*
• Выплачено: *{stats['paid_earnings']} ₽*

*✨ Статус выплат:*
"""
    
    if stats['available_earnings'] > 0:
        stats_text += f"\n💵 У тебя есть *{stats['available_earnings']} ₽* доступных для вывода!\n\nИспользуй кнопку \"💸 Запросить выплату\" чтобы запросить выплату."
    elif stats['requested_earnings'] > 0:
        stats_text += f"\n📤 Запрошено на выплату: *{stats['requested_earnings']} ₽*\n\nЗапрос отправлен в админскую группу. Выплата будет произведена в ближайшее время."
    elif stats['paid_earnings'] > 0:
        stats_text += f"\n✅ Выплачено: *{stats['paid_earnings']} ₽*"
    else:
        stats_text += "\n💡 Пока нет доступных средств для вывода."
    
    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_referral_payout_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать запрос на выплату"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    stats = db.get_referral_stats(user.id)
    
    if stats['available_earnings'] <= 0:
        await query.edit_message_text(
            "❌ *Нет доступных средств*\n\n"
            "У тебя нет средств, доступных для вывода.\n"
            "Комиссия начисляется автоматически после покупки твоим рефералом.",
            reply_markup=InlineKeyboardMarkup(get_back_button()),
            parse_mode='Markdown'
        )
        return
    
    if stats['available_earnings'] < REFERRAL_MIN_PAYOUT:
        await query.edit_message_text(
            f"❌ *Минимальная сумма вывода — {REFERRAL_MIN_PAYOUT:.0f} ₽*\n\n"
            f"💵 Доступно: *{stats['available_earnings']:.2f} ₽*\n"
            f"💰 Осталось накопить: *{REFERRAL_MIN_PAYOUT - stats['available_earnings']:.2f} ₽*\n\n"
            f"Приглашай друзей и зарабатывай!",
            reply_markup=InlineKeyboardMarkup(get_back_button()),
            parse_mode='Markdown'
        )
        return
    
    # Запрашиваем выплату в базе данных
    requested_amount = db.request_payout(user.id)
    
    if not requested_amount:
        await query.edit_message_text(
            "❌ *Ошибка*\n\n"
            "Не удалось запросить выплату. Попробуй позже или обратись в поддержку.",
            reply_markup=InlineKeyboardMarkup(get_back_button()),
            parse_mode='Markdown'
        )
        return
    
    # Отправляем запрос в админскую группу
    if ADMIN_CHAT_ID:
        try:
            user_info = f"👤 *Пользователь:* {user.first_name or ''} {user.last_name or ''}".strip()
            if user.username:
                user_info += f" (@{user.username})"
            user_info += f"\n🆔 *ID:* `{user.id}`"
            
            payout_text = f"""
📊 *ЗАПРОС НА ВЫПЛАТУ ПО ПАРТНЕРСКОЙ ПРОГРАММЕ*

{user_info}

💵 *Сумма к выплате:* *{requested_amount} ₽*

📊 *Статистика пользователя:*
• Всего рефералов: {stats['total_referrals']}
• Совершили покупку: {stats['total_purchases']}
• Общий заработок: {stats['total_earnings']} ₽
• Выплачено ранее: {stats['paid_earnings']} ₽

💸 *Действие:* Выплатить {requested_amount} ₽ пользователю
"""
            
            if ADMIN_CHAT_ID.startswith('@'):
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=payout_text,
                    parse_mode='Markdown'
                )
            else:
                admin_chat_id = int(ADMIN_CHAT_ID)
                await context.bot.send_message(
                    chat_id=admin_chat_id,
                    text=payout_text,
                    parse_mode='Markdown'
                )
            
            logger.info(f"Запрос на выплату отправлен в админскую группу: user_id={user.id}, amount={requested_amount}₽")
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса на выплату в админскую группу: {e}")
    
    success_text = f"""
✅ *Запрос на выплату отправлен!*

💵 *Сумма:* *{requested_amount} ₽*

📤 Запрос отправлен в админскую группу. Выплата будет произведена в ближайшее время.

💡 После выплаты статус обновится автоматически. Следи за статистикой через /referral
"""
    
    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        success_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_referral_copy_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать кнопку копирования реферальной ссылки"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем код из callback_data
    if query.data.startswith("referral_copy_"):
        referral_code = query.data.replace("referral_copy_", "")
    else:
        user = query.from_user
        referral_code = db.get_referral_code(user.id)
        if not referral_code:
            referral_code = db.create_referral_code(user.id)
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    await query.answer(
        f"🔗 Реферальная ссылка скопирована!\n\n{referral_link}",
        show_alert=True
    )


async def myconfig_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /myconfig"""
    # Правильно получаем user из update (работает и для message и для callback_query)
    user = update.effective_user
    if not user:
        logger.error("Не удалось получить user из update")
        return
    
    user_data = db.get_user(user.id)

    if not user_data:
        text = "☁️ У вас пока нет подписки.\n\n"
        text += "☁️ Оформите: /buy"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup
            )
        return

    # Проверяем активность подписки
    is_active = db.check_user_active(user.id)

    if not is_active:
        expiry_date = datetime.fromisoformat(user_data['expiry_date']).strftime("%d.%m.%Y")
        
        # Отключаем клиента в 3X-UI и деактивируем в базе
        if xui_manager and user_data.get('xray_email'):
            try:
                xui_manager.disable_client(user_data['xray_email'])
                logger.info(f"✅ Клиент отключён в 3X-UI для user_id={user.id}")
            except Exception as e:
                logger.error(f"Ошибка отключения клиента: {e}")
        
        db.deactivate_user(user.id)
        
        text = f"⏰ Подписка истекла {expiry_date}.\n\n"
        text += "☁️ Продлите: /buy"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup
            )
        return

    # Получаем UUID, email и строим ссылки
    xray_uuid = user_data.get('xray_uuid')
    xray_email = user_data.get('xray_email')
    vless_link = user_data.get('vless_link')

    if not xray_uuid:
        text = "❌ Конфиг не найден. 💬 /support"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    # Строим subscription URL из email
    sub_url = xui_manager.get_subscription_url(xray_email) if xui_manager and xray_email else None
    if not sub_url and vless_link:
        sub_url = vless_link  # fallback на vless если xui недоступен

    if not sub_url:
        text = "❌ Конфиг не найден. 💬 /support"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    expiry_date = datetime.fromisoformat(user_data['expiry_date']).strftime("%d.%m.%Y")
    chat_id = user.id
    
    # Количество устройств
    device_count = db.get_active_device_count(user.id)
    devices_text = f"📱 *Устройства:* {device_count}/3"

    # Отправляем информацию
    info_text = f"""
📄 *Ваш конфиг — {BOT_NAME}*

✅ Подписка активна
☁️ *Тариф:* {TARIFFS[user_data['subscription_type']]['name']}
📅 *До:* {expiry_date}
{devices_text}

Отправляю QR-код и ссылку на подписку 👇
"""
    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            info_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            info_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # 1. QR-код подписки
    if QRCODE_AVAILABLE:
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(sub_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(img_byte_arr, filename="config_qr.png"),
                caption="📱 *QR-код подписки для Happ*\n\nHapp → «+» → «Отсканировать QR» → наведите камеру\n\n_Будет показан заголовок, трафик и срок подписки_",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка генерации QR-кода: {e}")
    else:
        logger.warning("QR-код не отправлен: модуль qrcode не установлен или нет subscription URL")

    # 2. Инструкции
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_connection_instructions(),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка отправки инструкций: {e}")

    # 3. Subscription URL
    if sub_url:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📋 *Ссылка-подписка (для Happ — с метаданными):*\n\n`{sub_url}`\n\n_Скопируйте → Happ → «+» → «Добавить подписку по URL»_",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки subscription URL: {e}")


async def devices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /devices — показать устройства пользователя"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        text = "☁️ У вас пока нет подписки.\n\n☁️ Оформите: /buy"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    is_active = db.check_user_active(user.id)
    if not is_active:
        text = "⏰ Подписка истекла.\n\n☁️ Продлите: /buy"
        keyboard = get_back_button()
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    devices = db.get_user_devices(user.id)
    device_count = len(devices)

    text = f"📱 *Ваши устройства — {BOT_NAME}*\n\n"
    text += f"📊 *Использовано:* {device_count}/3\n\n"

    if devices:
        text += "*Активные устройства:*\n"
        for i, dev in enumerate(devices, 1):
            name = dev.get('device_name') or f"Устройство {i}"
            ip = dev.get('device_ip') or "неизвестен"
            last_seen = datetime.fromisoformat(dev['last_seen']).strftime("%d.%m.%Y %H:%M")
            text += f"  {i}. {name}\n     IP: `{ip}`\n     Последнее подключение: {last_seen}\n\n"
    else:
        text += "_Устройства ещё не подключались к VPN.\nКогда вы подключитесь — они появятся здесь._\n\n"

    text += "💡 *Лимит:* до 3 устройств одновременно\n"
    text += "🔗 Используйте одну подписку на всех устройствах."

    keyboard = get_back_button()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def handle_crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик оплаты через CryptoCloud"""
    query = update.callback_query
    user = query.from_user
    tariff_type = context.user_data.get('selected_tariff')
    tariff_info = TARIFFS.get(tariff_type)

    logger.info(f"handle_crypto_payment called: user={user.id}, tariff={tariff_type}")

    if not tariff_info:
        logger.warning(f"No tariff selected for user={user.id}")
        await query.edit_message_text("❌ Ошибка: тариф не выбран. Начните заново: /buy")
        return

    if tariff_type == "trial":
        await query.edit_message_text("🎁 Пробный период бесплатный — оплата не требуется!")
        return

    await query.edit_message_text("🪙 Создаю счет на оплату криптой...")

    order_id = create_cryptocloud_order_id(user.id, tariff_type)
    amount_usd = tariff_info['price'] / 90.0  # rough RUB to USD
    amount_usd = round(max(amount_usd, 1.0), 2)  # minimum $1
    logger.info(f"Creating CryptoCloud invoice: user={user.id}, order={order_id}, amount={amount_usd}")

    try:
        result = cryptocloud.create_invoice(
            amount=amount_usd,
            order_id=order_id,
            currency="USD"
        )
        logger.info(f"CryptoCloud API result: {result is not None}")

        if result and result.get('link'):
            link = result['link']
            uuid = result.get('uuid', 'N/A')
            logger.info(f"CryptoCloud link: {link}, uuid: {uuid}")

            text = f"""
🪙 *Оплата криптовалютой / TON / USDT — {BOT_NAME}*

☁️ *Тариф:* {tariff_info['name']}
💰 *Сумма:* ~{amount_usd} USD

*Как оплатить:*
1. Нажмите *«Перейти к оплате»* ниже
2. Выберите удобную криптовалюту на странице (USDT, TON, BTC и др.)
3. Отправьте точную сумму на указанный адрес или сканируйте QR
4. После подтверждения сети (обычно 5–30 минут) подписка активируется автоматически

💡 *Подсказка:* для быстрой оплаты выберите *TON* или *USDT TRC20* — комиссия минимальная.
"""
            keyboard = [
                [InlineKeyboardButton("🪙 Перейти к оплате", url=link)],
            ] + get_back_button()
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"CryptoCloud invoice shown to user={user.id}, order={order_id}, link={link}")
        else:
            logger.error(f"CryptoCloud create_invoice returned empty result for user={user.id}")
            await query.edit_message_text(
                "❌ Не удалось создать счет. Попробуйте оплатить картой (ЮMoney) или 💬 /support"
            )
    except Exception as e:
        logger.error(f"CryptoCloud payment error for user={user.id}: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Ошибка при создании счета. Попробуйте позже или 💬 /support"
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на inline кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("tariff_"):
        await handle_tariff_selection(update, context)
    elif query.data == "pay_crypto":
        await handle_crypto_payment(update, context)
    elif query.data == "check_status":
        await status_command(update, context)
    elif query.data == "my_config":
        await myconfig_command(update, context)
    elif query.data == "my_devices":
        await devices_command(update, context)
    elif query.data == "support":
        await support_command(update, context)
    elif query.data == "instruction":
        await instruction_command(update, context)
    elif query.data == "privacy":
        await privacy_command(update, context)
    elif query.data == "user_stats":
        await stats_command(update, context)
    elif query.data == "referral_program":
        await referral_command(update, context)
    elif query.data == "referral_stats":
        await handle_referral_stats(update, context)
    elif query.data == "referral_request_payout":
        await handle_referral_payout_request(update, context)
    elif query.data.startswith("referral_copy_"):
        await handle_referral_copy_link(update, context)
    elif query.data == "back_to_start":
        user = update.effective_user
        welcome_text = get_welcome_text(user.first_name)
        reply_markup = get_main_keyboard(include_referral=True, user_id=user.id)
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif query.data == "cancel" or query.data == "cancel_payment":
        await query.edit_message_text("↩️ Операция отменена. Меню: /start")
        return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены"""
    await update.message.reply_text("↩️ Операция отменена. Меню: /start")
    context.user_data.clear()
    return ConversationHandler.END


# Состояния для рассылки
WAITING_BROADCAST_MESSAGE = 2


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /broadcast для рассылки сообщений всем пользователям"""
    chat = update.effective_chat
    
    # Проверка, что команда отправлена из админской группы
    if ADMIN_CHAT_ID:
        try:
            admin_chat_id = int(ADMIN_CHAT_ID)
            if chat.id != admin_chat_id:
                await update.message.reply_text("❌ Эта команда доступна только из админской группы!")
                return
        except ValueError:
            # Если ADMIN_CHAT_ID это username, проверяем по username
            if hasattr(chat, 'username') and chat.username and ADMIN_CHAT_ID.startswith('@'):
                if chat.username.lower() != ADMIN_CHAT_ID.lower().replace('@', ''):
                    await update.message.reply_text("❌ Эта команда доступна только из админской группы!")
                    return
    
    # Проверка, что отправитель - администратор группы
    if chat.type in ['group', 'supergroup']:
        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Только администраторы могут использовать рассылку!")
            return
    
    await update.message.reply_text(
        "📢 *Рассылка сообщений*\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям бота.\n"
        "Можно отправить текст, фото, видео или документ.\n\n"
        "Для отмены используйте /cancel",
        parse_mode='Markdown'
    )
    return WAITING_BROADCAST_MESSAGE


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщения для рассылки"""
    chat = update.effective_chat
    
    # Повторная проверка админской группы
    if ADMIN_CHAT_ID:
        try:
            admin_chat_id = int(ADMIN_CHAT_ID)
            if chat.id != admin_chat_id:
                return ConversationHandler.END
        except ValueError:
            if hasattr(chat, 'username') and chat.username and ADMIN_CHAT_ID.startswith('@'):
                if chat.username.lower() != ADMIN_CHAT_ID.lower().replace('@', ''):
                    return ConversationHandler.END
    
    # Получаем все user_id из базы данных
    all_users = db.get_all_users()
    
    if not all_users:
        await update.message.reply_text("❌ В базе данных нет пользователей для рассылки!")
        return ConversationHandler.END
    
    # Отправляем уведомление о начале рассылки
    status_msg = await update.message.reply_text(f"📤 Начинаю рассылку для {len(all_users)} пользователей...")
    
    successful = 0
    failed = 0
    
    # Отправляем сообщение всем пользователям
    for user_id in all_users:
        try:
            # Определяем тип сообщения и отправляем
            if update.message.text:
                await context.bot.send_message(chat_id=user_id, text=update.message.text, parse_mode='Markdown')
            elif update.message.photo:
                await context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video:
                await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id, caption=update.message.caption)
            elif update.message.document:
                await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id, caption=update.message.caption)
            else:
                # Для других типов отправляем как есть
                await context.bot.copy_message(chat_id=user_id, from_chat_id=chat.id, message_id=update.message.message_id)
            
            successful += 1
        except Exception as e:
            failed += 1
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    
    # Обновляем статус
    await status_msg.edit_text(
        f"✅ *Рассылка завершена!*\n\n"
        f"📊 Статистика:\n"
        f"✅ Отправлено: {successful}\n"
        f"❌ Ошибок: {failed}\n"
        f"📱 Всего пользователей: {len(all_users)}",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END


async def handle_user_message_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылка сообщений пользователей в админскую группу"""
    message = update.message
    
    # Проверяем, что это приватное сообщение от пользователя (не бота)
    if not message or message.chat.type != 'private':
        return
    
    # Пропускаем команды (они обрабатываются отдельно)
    if message.text and message.text.startswith('/'):
        return
    
    # Пропускаем ответы бота (чтобы не было зацикливания)
    if message.from_user and message.from_user.is_bot:
        return
    
    # Проверяем, что админская группа настроена
    if not ADMIN_CHAT_ID:
        return
    
    # Пропускаем сообщения, которые обрабатываются другими ConversationHandler
    # (например, фото платежей в состоянии WAITING_PAYMENT)
    # Если в user_data есть ключи, связанные с покупкой, значит это часть процесса оплаты
    if context.user_data.get('selected_tariff') or context.user_data.get('payment_comment'):
        # Это сообщение обрабатывается ConversationHandler для покупки
        return
    
    user = message.from_user
    user_info = f"👤 Пользователь: {user.first_name or ''} {user.last_name or ''}".strip()
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f"\n🆔 ID: {user.id}"
    
    try:
        # Пересылаем сообщение в админскую группу
        if ADMIN_CHAT_ID.startswith('@'):
            # Если это username группы
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{user_info}\n\n⬇️ Сообщение от пользователя:",
                parse_mode='Markdown'
            )
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        else:
            # Если это ID группы
            admin_chat_id = int(ADMIN_CHAT_ID)
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"{user_info}\n\n⬇️ Сообщение от пользователя:",
                parse_mode='Markdown'
            )
            await context.bot.forward_message(
                chat_id=admin_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
    except Exception as e:
        logger.error(f"Ошибка пересылки сообщения пользователя в админскую группу: {e}")


async def handle_admin_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений из админской группы - автоматическая пересылка пользователям"""
    message = update.message
    
    # Проверяем, что это сообщение из группы
    if not message or message.chat.type not in ['group', 'supergroup']:
        return
    
    chat = message.chat
    
    # Проверка, что сообщение из админской группы
    if ADMIN_CHAT_ID:
        try:
            admin_chat_id = int(ADMIN_CHAT_ID)
            if chat.id != admin_chat_id:
                return
        except ValueError:
            # Если ADMIN_CHAT_ID это username, проверяем по username
            if hasattr(chat, 'username') and chat.username and ADMIN_CHAT_ID.startswith('@'):
                if chat.username.lower() != ADMIN_CHAT_ID.lower().replace('@', ''):
                    return
    
    # Пропускаем команды и служебные сообщения
    if message.text and message.text.startswith('/'):
        return
    
    # Пропускаем ответы бота (чтобы не было зацикливания)
    if message.from_user and message.from_user.is_bot:
        return
    
    # Проверяем, что отправитель - администратор группы
    try:
        member = await context.bot.get_chat_member(chat.id, message.from_user.id)
        if member.status not in ['administrator', 'creator']:
            return
    except Exception as e:
        logger.error(f"Ошибка проверки администратора: {e}")
        return
    
    # Получаем всех пользователей из базы данных
    all_users = db.get_all_users()
    
    if not all_users:
        return
    
    successful = 0
    failed = 0
    
    # Пересылаем сообщение всем пользователям
    for user_id in all_users:
        try:
            # Используем copy_message для сохранения исходного формата
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=chat.id,
                message_id=message.message_id
            )
            successful += 1
        except Exception as e:
            failed += 1
            logger.debug(f"Ошибка пересылки сообщения пользователю {user_id}: {e}")
    
    # Отправляем статус в админскую группу (тихо, чтобы не засорять чат)
    if failed > 0:
        logger.info(f"Рассылка из админской группы: отправлено {successful}, ошибок {failed} из {len(all_users)} пользователей")


def main():
    """Главная функция запуска бота"""
    global xui_manager

    # Проверка конфигурации
    if SERVER_IP == "YOUR_SERVER_IP":
        logger.error(
            "❌ ОШИБКА: Не настроен IP сервера!\n"
            "Установите переменную окружения SERVER_IP или отредактируйте bot.py\n"
            "Используйте скрипт setup_server.py для автоматического определения IP"
        )
        sys.exit(1)

    # Инициализация 3X-UI менеджера
    global xui_manager
    try:
        xui_manager = XUIManager()
        logger.info(f"✅ 3X-UI менеджер инициализирован (сервер: {SERVER_IP})")
    except Exception as e:
        logger.error(f"Ошибка инициализации 3X-UI менеджера: {e}")
        logger.warning("⚠️ Бот запустится, но создание конфигов будет недоступно до подключения к 3X-UI")

    # Проверка токена ЮMoney
    if USE_YOOMONEY_API and not YMONEY_ACCESS_TOKEN:
        logger.warning(
            "⚠️ ВНИМАНИЕ: Токен API ЮMoney не установлен!\n"
            "Бот будет работать в режиме ручной проверки платежей через скриншоты.\n"
            "Для автоматической проверки платежей через API:\n"
            "1. Запустите: python yoomoney_oauth.py\n"
            "2. Следуйте инструкции: YOOMONEY_SOYKA_VPN.md\n"  # TODO: переименовать файл
            "3. Установите токен: export YMONEY_ACCESS_TOKEN=\"ваш_токен\"\n"
        )
    elif USE_YOOMONEY_API and YMONEY_ACCESS_TOKEN:
        logger.info("✅ Токен API ЮMoney установлен. Автоматическая проверка платежей включена.")
    else:
        logger.info("ℹ️ API ЮMoney отключен. Режим ручной проверки через скриншоты.")

    # Создаем приложение с настройкой меню команд
    async def post_init(app: Application) -> None:
        """Функция для настройки меню команд при инициализации"""
        commands = [
            BotCommand("start", f"☁️ {BOT_NAME} — меню"),
            BotCommand("buy", "☁️ Подключить VPN"),
            BotCommand("instruction", "📖 Инструкция"),
            BotCommand("myconfig", "📄 Мой конфиг"),
            BotCommand("status", "⚡ Статус VPN"),
            BotCommand("support", "💬 Поддержка"),
            BotCommand("stats", "👥 Пользователи"),
            BotCommand("referral", "💰 Партнёрка"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("✅ Меню команд установлено")

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Обработчик покупки с ConversationHandler (только для приватных чатов)
    buy_handler = ConversationHandler(
        entry_points=[
            CommandHandler('buy', buy_command, filters=filters.ChatType.PRIVATE),
            CallbackQueryHandler(buy_command, pattern="^buy_vpn$"),
            CallbackQueryHandler(handle_tariff_selection, pattern="^tariff_")
        ],
        states={
            WAITING_PAYMENT: [
                CallbackQueryHandler(handle_tariff_selection, pattern="^tariff_"),
                CallbackQueryHandler(handle_check_payment_button, pattern="^check_payment$"),
                CallbackQueryHandler(handle_crypto_payment, pattern="^pay_crypto$"),
                MessageHandler(filters.PHOTO, handle_payment_screenshot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment_screenshot),
            ]
        },
        fallbacks=[
            CommandHandler('buy', buy_command, filters=filters.ChatType.PRIVATE),
            CommandHandler('cancel', cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern="^cancel")
        ]
    )

    # Обработчик рассылки с ConversationHandler
    broadcast_handler = ConversationHandler(
        entry_points=[
            CommandHandler('broadcast', broadcast_command),
        ],
        states={
            WAITING_BROADCAST_MESSAGE: [
                MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast_message)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handler)
        ]
    )

    # Регистрируем обработчики (только для приватных чатов)
    private_chat_filter = filters.ChatType.PRIVATE
    
    # Сначала регистрируем команды и ConversationHandler (они имеют приоритет)
    application.add_handler(CommandHandler('start', start_command, filters=private_chat_filter))
    application.add_handler(buy_handler)  # buy_handler уже настроен для приватных чатов через entry_points
    application.add_handler(broadcast_handler)  # Обработчик рассылки (только для админов)
    application.add_handler(CommandHandler('instruction', instruction_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('status', status_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('support', support_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('myconfig', myconfig_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('privacy', privacy_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('stats', stats_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('referral', referral_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('resettrial', resettrial_command, filters=private_chat_filter))
    application.add_handler(CommandHandler('devices', devices_command, filters=private_chat_filter))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Затем регистрируем обработчик пересылки сообщений пользователей в админскую группу
    # Важно: этот обработчик должен быть ПОСЛЕ ConversationHandler, чтобы не перехватывать сообщения процесса покупки
    # Перехватывает все сообщения из приватных чатов (кроме команд) и пересылает в админскую группу
    user_message_filter = filters.ChatType.PRIVATE & ~filters.COMMAND
    application.add_handler(MessageHandler(user_message_filter, handle_user_message_to_admin))
    
    # Обработчик автоматической пересылки сообщений из админской группы
    # Перехватывает все сообщения из группы (кроме команд и сообщений от бота) и пересылает пользователям
    admin_group_filter = filters.ChatType.GROUPS & ~filters.COMMAND
    application.add_handler(MessageHandler(admin_group_filter, handle_admin_group_message))

    # Запускаем HTTP сервер для конфигов в отдельном потоке
    def run_config_server():
        config_server.run_server(host='0.0.0.0', port=5000, debug=False)

    server_thread = threading.Thread(target=run_config_server, daemon=True)
    server_thread.start()
    logger.info("HTTP сервер для конфигов запущен на порту 5000")

    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

