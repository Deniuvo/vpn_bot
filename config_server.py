"""
HTTP сервер для раздачи WireGuard конфигов и приема POSTBACK уведомлений
Можно использовать Flask для разработки или настроить nginx для продакшена
"""
from flask import Flask, send_file, abort, request, jsonify
import os
import logging
import jwt

# Импортируем базу данных для проверки активности подписки
try:
    from database import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("База данных недоступна - проверка подписки отключена")

app = Flask(__name__)
CONFIGS_DIR = "configs"

# CryptoCloud POSTBACK secret
CRYPTOCLOUD_SECRET = os.getenv(
    "CRYPTOCLOUD_SECRET",
    "2zckVOgcWOGLseYPF9jVQ3B29HopsFVIzva5"
)


@app.route('/config/<int:user_id>')
def get_config(user_id: int):
    """
    Эндпоинт для получения WireGuard конфига по user_id
    Проверяет, что подписка активна
    Доступ: http://your-server-ip:5000/config/<user_id>
    """
    # Проверяем .conf файл (WireGuard конфиг)
    config_path = os.path.join(CONFIGS_DIR, f"{user_id}.conf")
    
    if not os.path.exists(config_path):
        abort(404)

    # Проверяем активность подписки
    if DB_AVAILABLE:
        is_active = db.check_user_active(user_id)
        if not is_active:
            # Подписка истекла - не отдаем конфиг
            abort(403)  # Forbidden

        # Регистрируем/обновляем устройство пользователя
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
        # Берем первый IP если X-Forwarded-For содержит несколько
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')
        device_name = None
        if user_agent:
            # Простая эвристика для имени устройства по User-Agent
            ua = user_agent.lower()
            if 'iphone' in ua:
                device_name = 'iPhone'
            elif 'ipad' in ua:
                device_name = 'iPad'
            elif 'android' in ua:
                device_name = 'Android'
            elif 'windows' in ua:
                device_name = 'Windows'
            elif 'macintosh' in ua or 'mac os' in ua:
                device_name = 'macOS'
            elif 'linux' in ua:
                device_name = 'Linux'
        try:
            db.add_or_update_device(user_id, client_ip, device_name)
        except Exception as e:
            logging.warning(f"Failed to track device for user={user_id}: {e}")

    return send_file(
        config_path,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"wg_{user_id}.conf"
    )


@app.route('/webhook/cryptocloud', methods=['POST'])
def cryptocloud_postback():
    """
    POSTBACK эндпоинт для CryptoCloud
    Получает уведомление об оплате и выдает подписку
    """
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        logging.info(f"CryptoCloud POSTBACK received: {data}")

        # Verify JWT token if present
        token = data.get('token')
        if token:
            try:
                jwt.decode(token, CRYPTOCLOUD_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                logging.warning("CryptoCloud POSTBACK token expired")
            except jwt.InvalidTokenError as e:
                logging.warning(f"CryptoCloud POSTBACK token invalid: {e}")

        status = data.get('status')
        invoice_id = data.get('invoice_id')
        order_id = data.get('order_id')

        if status != 'success' or not order_id:
            return jsonify({"status": "ignored"}), 200

        # Parse order_id: vpn_{user_id}_{tariff_type}_{timestamp}
        parts = order_id.split('_')
        if len(parts) < 4 or parts[0] != 'vpn':
            logging.warning(f"CryptoCloud invalid order_id format: {order_id}")
            return jsonify({"status": "bad_order_id"}), 400

        try:
            user_id = int(parts[1])
            tariff_type = parts[2]
        except (ValueError, IndexError):
            logging.warning(f"CryptoCloud failed to parse order_id: {order_id}")
            return jsonify({"status": "parse_error"}), 400

        # Activate subscription in database
        if DB_AVAILABLE:
            try:
                # Check if user already has active subscription
                user = db.get_user(user_id)
                expiry = db.add_or_extend_subscription(user_id, tariff_type)
                logging.info(f"CryptoCloud subscription activated: user_id={user_id}, tariff={tariff_type}, expiry={expiry}")
            except Exception as e:
                logging.error(f"CryptoCloud failed to activate subscription: {e}")
                return jsonify({"status": "db_error"}), 500
        else:
            logging.warning("DB not available, cannot activate subscription")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"CryptoCloud POSTBACK error: {e}")
        return jsonify({"status": "error"}), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запуск Flask сервера для раздачи конфигов"""
    if not os.path.exists(CONFIGS_DIR):
        os.makedirs(CONFIGS_DIR)

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Для тестирования можно запустить напрямую
    run_server(debug=True)

