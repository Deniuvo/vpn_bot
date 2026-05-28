"""
Трекер устройств — обновляет user_devices в vpn_bot.db на основе IP из 3X-UI client_traffics.
Запускать по cron каждые 5 минут:
    */5 * * * * cd /root/vpn_bot && /root/vpn_bot/venv/bin/python device_tracker.py >> /root/vpn_bot/logs/device_tracker.log 2>&1
"""
import sqlite3
import os
import logging
from datetime import datetime

# Пути к базам данных
XUI_DB = "/etc/x-ui/x-ui.db"
BOT_DB = "vpn_bot.db"

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_xui_client_ips():
    """Получить email -> ip из 3X-UI client_traffics"""
    if not os.path.exists(XUI_DB):
        logger.warning(f"3X-UI БД не найдена: {XUI_DB}")
        return {}

    try:
        conn = sqlite3.connect(XUI_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT email, ip FROM client_traffics WHERE ip IS NOT NULL AND ip != ''")
        results = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Ошибка чтения 3X-UI БД: {e}")
        return {}


def update_bot_devices(email_to_ip: dict):
    """Обновить user_devices в vpn_bot.db"""
    if not os.path.exists(BOT_DB):
        logger.warning(f"Бот БД не найдена: {BOT_DB}")
        return

    try:
        conn = sqlite3.connect(BOT_DB)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        updated = 0
        inserted = 0

        for email, ip in email_to_ip.items():
            if not email or not ip:
                continue

            # email формат: vpn_<user_id>
            if not email.startswith("vpn_"):
                continue

            try:
                user_id = int(email.split("_")[1])
            except (ValueError, IndexError):
                continue

            # Проверяем, есть ли уже запись
            cursor.execute(
                "SELECT id FROM user_devices WHERE user_id = ? AND device_ip = ?",
                (user_id, ip)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE user_devices SET last_seen = ? WHERE id = ?",
                    (now, existing[0])
                )
                updated += 1
            else:
                cursor.execute(
                    "INSERT INTO user_devices (user_id, device_ip, device_name, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)",
                    (user_id, ip, None, now, now)
                )
                inserted += 1

        conn.commit()
        conn.close()
        logger.info(f"Устройства обновлены: {updated} обновлено, {inserted} добавлено")
    except Exception as e:
        logger.error(f"Ошибка обновления bot БД: {e}")


def cleanup_old_devices(days: int = 30):
    """Очистить устройства, неактивные более N дней"""
    if not os.path.exists(BOT_DB):
        return

    try:
        conn = sqlite3.connect(BOT_DB)
        cursor = conn.cursor()
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("DELETE FROM user_devices WHERE last_seen < ?", (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            logger.info(f"Очищено старых устройств: {deleted}")
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")


def main():
    logger.info("=== Запуск трекера устройств ===")
    email_to_ip = get_xui_client_ips()
    logger.info(f"Найдено клиентов с IP: {len(email_to_ip)}")

    if email_to_ip:
        update_bot_devices(email_to_ip)

    cleanup_old_devices(days=30)
    logger.info("=== Готово ===")


if __name__ == "__main__":
    main()
