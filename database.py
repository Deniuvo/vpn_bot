"""
Модуль для работы с базой данных SQLite
Хранит информацию о пользователях, подписках и конфигах
"""
import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

DB_NAME = "vpn_bot.db"

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.init_db()

    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscription_type TEXT,
                payment_date TEXT,
                expiry_date TEXT,
                config_url TEXT,
                is_active INTEGER DEFAULT 1,
                config_path TEXT,
                private_key TEXT,
                public_key TEXT,
                ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица IP адресов для отслеживания занятых
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_ips (
                ip_address TEXT PRIMARY KEY,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Таблица реферальных ссылок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_links (
                user_id INTEGER PRIMARY KEY,
                referral_code TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Таблица отслеживания рефералов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                referral_code TEXT NOT NULL,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                purchased_at TEXT,
                purchase_amount REAL,
                commission_amount REAL,
                commission_paid INTEGER DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        """)

        # Таблица заработков и запросов на выплату
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                referral_id INTEGER,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, paid, requested
                requested_at TEXT,
                paid_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (referral_id) REFERENCES referrals (id)
            )
        """)

        # Таблица устройств пользователя (до 3 одновременно)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_ip TEXT,
                device_name TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_user ON user_devices(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_ip ON user_devices(device_ip)")

        # Создаем индексы для быстрого поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_code ON referrals(referral_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_earnings_user ON referral_earnings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_earnings_status ON referral_earnings(status)")

        # Миграция: добавляем колонки для Xray/VLESS (если ещё нет)
        for col, col_type in [("xray_uuid", "TEXT"), ("xray_email", "TEXT"), ("vless_link", "TEXT")]:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # колонка уже существует

        conn.commit()
        conn.close()

    def get_connection(self):
        """Получить соединение с базой данных"""
        return sqlite3.connect(DB_NAME)

    def add_user(self, user_id: int, username: str, subscription_type: str,
                 xray_uuid: str = None, xray_email: str = None, vless_link: str = None,
                 config_path: str = None, private_key: str = None,
                 public_key: str = None, ip_address: str = None) -> bool:
        """Добавить пользователя в базу данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Определяем срок подписки
            subscription_days = {
                "trial": 2,  # 2 дня для trial
                "1_month": 30,
                "3_months": 90,
                "1_year": 365
            }
            days = subscription_days.get(subscription_type, 30)

            payment_date = datetime.now().isoformat()
            expiry_date = (datetime.now() + timedelta(days=days)).isoformat()

            cursor.execute("""
                INSERT INTO users (user_id, username, subscription_type, payment_date,
                                 expiry_date, config_path, private_key, public_key, ip_address,
                                 xray_uuid, xray_email, vless_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, subscription_type, payment_date, expiry_date,
                  config_path, private_key, public_key, ip_address,
                  xray_uuid, xray_email, vless_link))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        finally:
            conn.close()


    def get_user(self, user_id: int) -> Optional[dict]:
        """Получить информацию о пользователе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def update_user_config(self, user_id: int, config_url: str):
        """Обновить URL конфига пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET config_url = ? WHERE user_id = ?
        """, (config_url, user_id))

        conn.commit()
        conn.close()

    def update_user_subscription(self, user_id: int, username: str, subscription_type: str,
                                 xray_uuid: str = None, xray_email: str = None, vless_link: str = None,
                                 config_path: str = None, private_key: str = None,
                                 public_key: str = None, ip_address: str = None) -> bool:
        """Обновить подписку существующего пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Определяем срок подписки
            subscription_days = {
                "trial": 2,  # 2 дня для trial
                "1_month": 30,
                "3_months": 90,
                "1_year": 365
            }
            days = subscription_days.get(subscription_type, 30)

            payment_date = datetime.now().isoformat()
            expiry_date = (datetime.now() + timedelta(days=days)).isoformat()

            # Обновляем данные пользователя
            cursor.execute("""
                UPDATE users 
                SET username = ?, subscription_type = ?, payment_date = ?,
                    expiry_date = ?, xray_uuid = ?, xray_email = ?,
                    vless_link = ?, is_active = 1
                WHERE user_id = ?
            """, (username, subscription_type, payment_date, expiry_date,
                  xray_uuid, xray_email, vless_link, user_id))

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления подписки пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_or_extend_subscription(self, user_id: int, subscription_type: str) -> str:
        """
        Добавить или продлить подписку пользователя.
        Если подписка активна — продлевает от текущей даты окончания.
        Возвращает новую дату окончания (ISO format).
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            subscription_days = {
                "trial": 2,
                "1_month": 30,
                "3_months": 90,
                "1_year": 365
            }
            days = subscription_days.get(subscription_type, 30)

            # Check existing subscription
            cursor.execute(
                "SELECT expiry_date FROM users WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            row = cursor.fetchone()

            now = datetime.now()
            if row:
                current_expiry = datetime.fromisoformat(row[0])
                if current_expiry > now:
                    # Extend from current expiry
                    new_expiry = current_expiry + timedelta(days=days)
                else:
                    # Expired, start from now
                    new_expiry = now + timedelta(days=days)
            else:
                new_expiry = now + timedelta(days=days)

            payment_date = now.isoformat()
            expiry_iso = new_expiry.isoformat()

            cursor.execute("""
                UPDATE users
                SET subscription_type = ?, payment_date = ?, expiry_date = ?, is_active = 1
                WHERE user_id = ?
            """, (subscription_type, payment_date, expiry_iso, user_id))

            conn.commit()
            return expiry_iso
        except Exception as e:
            logger.error(f"Ошибка продления подписки {user_id}: {e}", exc_info=True)
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_next_free_ip(self) -> Optional[str]:
        """Получить следующий свободный IP адрес из диапазона 10.0.0.2-254"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем все занятые IP
        cursor.execute("SELECT ip_address FROM used_ips")
        used_ips = {row[0] for row in cursor.fetchall()}

        # Ищем свободный IP в диапазоне 10.0.0.2 - 10.0.0.254
        for i in range(2, 255):
            ip = f"10.0.0.{i}"
            if ip not in used_ips:
                conn.close()
                return ip

        conn.close()
        return None

    def check_user_active(self, user_id: int) -> bool:
        """Проверить, активна ли подписка пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT expiry_date, is_active FROM users 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        expiry_date = datetime.fromisoformat(row[0])
        return datetime.now() < expiry_date

    def get_user_config_path(self, user_id: int) -> Optional[str]:
        """Получить путь к конфигу пользователя"""
        user = self.get_user(user_id)
        if user:
            return user.get('config_path')
        return None

    def get_all_users(self) -> list:
        """Получить список всех user_id из базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT user_id FROM users")
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users
    
    def get_expired_users(self) -> list:
        """Получить список пользователей с истекшей подпиской"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT user_id, username, expiry_date, public_key, ip_address, subscription_type
            FROM users 
            WHERE expiry_date < ? AND is_active = 1
        """, (now,))
        
        expired_users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return expired_users
    
    def deactivate_user(self, user_id: int) -> bool:
        """Деактивировать пользователя (пометить подписку как неактивную)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET is_active = 0 
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка деактивации пользователя {user_id}: {e}")
            return False
        finally:
            conn.close()

    def user_has_ever_had_trial(self, user_id: int) -> bool:
        """Проверить, получал ли пользователь когда-либо trial подписку (даже если истекла)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE user_id = ? AND subscription_type = 'trial'
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0

    def get_active_users_stats(self) -> dict:
        """Получить статистику по активным пользователям с разбивкой по тарифам"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        
        now = datetime.now().isoformat()
        
        # Общее количество активных пользователей
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM users 
            WHERE expiry_date > ? AND is_active = 1
        """, (now,))
        total_active = cursor.fetchone()[0]
        
        # Статистика по тарифам
        cursor.execute("""
            SELECT 
                subscription_type,
                COUNT(*) as count
            FROM users 
            WHERE expiry_date > ? AND is_active = 1
            GROUP BY subscription_type
        """, (now,))
        
        stats_by_tariff = {}
        for row in cursor.fetchall():
            stats_by_tariff[row['subscription_type']] = row['count']
        
        # Всего пользователей в базе (включая неактивных)
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_active': total_active,
            'total_users': total_users,
            'by_tariff': stats_by_tariff
        }

    def create_referral_code(self, user_id: int) -> str:
        """Создать уникальную реферальную ссылку для пользователя"""
        import hashlib
        import time
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже реферальный код
        cursor.execute("SELECT referral_code FROM referral_links WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        # Генерируем уникальный код
        timestamp = str(time.time())
        user_str = str(user_id)
        code_data = f"{user_str}_{timestamp}"
        referral_code = hashlib.md5(code_data.encode()).hexdigest()[:12]
        
        # Проверяем уникальность
        cursor.execute("SELECT COUNT(*) FROM referral_links WHERE referral_code = ?", (referral_code,))
        while cursor.fetchone()[0] > 0:
            timestamp = str(time.time())
            code_data = f"{user_str}_{timestamp}_{hashlib.md5(code_data.encode()).hexdigest()[:6]}"
            referral_code = hashlib.md5(code_data.encode()).hexdigest()[:12]
            cursor.execute("SELECT COUNT(*) FROM referral_links WHERE referral_code = ?", (referral_code,))
        
        # Сохраняем код
        cursor.execute("""
            INSERT INTO referral_links (user_id, referral_code)
            VALUES (?, ?)
        """, (user_id, referral_code))
        
        conn.commit()
        conn.close()
        return referral_code
    
    def get_referral_code(self, user_id: int) -> Optional[str]:
        """Получить реферальный код пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT referral_code FROM referral_links WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    def register_referral(self, referrer_id: int, referred_id: int, referral_code: str) -> bool:
        """Зарегистрировать реферала (когда пользователь переходит по ссылке)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем, не зарегистрирован ли уже этот реферал
            cursor.execute("""
                SELECT id FROM referrals 
                WHERE referred_id = ? AND referrer_id = ?
            """, (referred_id, referrer_id))
            
            if cursor.fetchone():
                conn.close()
                return False  # Уже зарегистрирован
            
            # Регистрируем реферала
            cursor.execute("""
                INSERT INTO referrals (referrer_id, referred_id, referral_code)
                VALUES (?, ?, ?)
            """, (referrer_id, referred_id, referral_code))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка регистрации реферала: {e}")
            conn.close()
            return False
    
    def get_referrer_by_code(self, referral_code: str) -> Optional[int]:
        """Получить ID пользователя по реферальному коду"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM referral_links WHERE referral_code = ?", (referral_code,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    def update_referral_purchase(self, referred_id: int, purchase_amount: float, commission_amount: float) -> bool:
        """Начислить комиссию за первый платный платёж реферала (повторные не учитываются)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Находим запись о реферале
            cursor.execute("""
                SELECT id, referrer_id FROM referrals 
                WHERE referred_id = ? AND purchased_at IS NULL
            """, (referred_id,))
            
            referral = cursor.fetchone()
            if not referral:
                conn.close()
                return False
            
            referral_id, referrer_id = referral
            
            # Обновляем информацию о покупке
            purchase_date = datetime.now().isoformat()
            cursor.execute("""
                UPDATE referrals 
                SET purchased_at = ?, purchase_amount = ?, commission_amount = ?
                WHERE id = ?
            """, (purchase_date, purchase_amount, commission_amount, referral_id))
            
            # Создаем запись о заработке
            cursor.execute("""
                INSERT INTO referral_earnings (user_id, referral_id, amount, status)
                VALUES (?, ?, ?, 'pending')
            """, (referrer_id, referral_id, commission_amount))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка обновления покупки реферала: {e}")
            conn.close()
            return False
    
    def get_referral_stats(self, user_id: int) -> dict:
        """Получить статистику по партнерской программе для пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Общее количество рефералов
        cursor.execute("""
            SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
        """, (user_id,))
        total_referrals = cursor.fetchone()[0]
        
        # Количество рефералов, которые совершили покупку
        cursor.execute("""
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND purchased_at IS NOT NULL
        """, (user_id,))
        total_purchases = cursor.fetchone()[0]
        
        # Общий заработок
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
            WHERE user_id = ?
        """, (user_id,))
        total_earnings = cursor.fetchone()[0] or 0
        
        # Доступно для вывода
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
            WHERE user_id = ? AND status = 'pending'
        """, (user_id,))
        available_earnings = cursor.fetchone()[0] or 0
        
        # Выплачено
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
            WHERE user_id = ? AND status = 'paid'
        """, (user_id,))
        paid_earnings = cursor.fetchone()[0] or 0
        
        # Запрошено на выплату
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
            WHERE user_id = ? AND status = 'requested'
        """, (user_id,))
        requested_earnings = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_referrals': total_referrals,
            'total_purchases': total_purchases,
            'total_earnings': round(total_earnings, 2),
            'available_earnings': round(available_earnings, 2),
            'paid_earnings': round(paid_earnings, 2),
            'requested_earnings': round(requested_earnings, 2)
        }
    
    def request_payout(self, user_id: int) -> Optional[float]:
        """Запросить выплату (меняет статус всех pending на requested)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем сумму для вывода
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
                WHERE user_id = ? AND status = 'pending'
            """, (user_id,))
            
            total_amount = cursor.fetchone()[0] or 0
            
            if total_amount <= 0:
                conn.close()
                return None
            
            # Меняем статус на requested
            requested_at = datetime.now().isoformat()
            cursor.execute("""
                UPDATE referral_earnings 
                SET status = 'requested', requested_at = ?
                WHERE user_id = ? AND status = 'pending'
            """, (requested_at, user_id))
            
            conn.commit()
            conn.close()
            return round(total_amount, 2)
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка запроса выплаты: {e}")
            conn.close()
            return None

    # ============== Devices ==============

    def add_or_update_device(self, user_id: int, device_ip: str, device_name: str = None) -> bool:
        """Добавить или обновить устройство пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        try:
            # Проверяем, есть ли уже это устройство
            cursor.execute("""
                SELECT id FROM user_devices 
                WHERE user_id = ? AND device_ip = ?
            """, (user_id, device_ip))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE user_devices 
                    SET last_seen = ?, device_name = COALESCE(?, device_name)
                    WHERE id = ?
                """, (now, device_name, existing[0]))
            else:
                cursor.execute("""
                    INSERT INTO user_devices (user_id, device_ip, device_name, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, device_ip, device_name, now, now))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка добавления устройства: {e}")
            return False
        finally:
            conn.close()

    def get_user_devices(self, user_id: int, active_days: int = 7) -> list:
        """Получить список устройств пользователя, активных за последние N дней"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row

        cutoff = (datetime.now() - timedelta(days=active_days)).isoformat()

        cursor.execute("""
            SELECT id, device_ip, device_name, first_seen, last_seen
            FROM user_devices
            WHERE user_id = ? AND last_seen > ?
            ORDER BY last_seen DESC
        """, (user_id, cutoff))

        devices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return devices

    def get_active_device_count(self, user_id: int, active_days: int = 7) -> int:
        """Получить количество активных устройств пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=active_days)).isoformat()

        cursor.execute("""
            SELECT COUNT(DISTINCT device_ip) FROM user_devices
            WHERE user_id = ? AND last_seen > ?
        """, (user_id, cutoff))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def remove_device(self, user_id: int, device_ip: str) -> bool:
        """Удалить конкретное устройство пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM user_devices WHERE user_id = ? AND device_ip = ?
            """, (user_id, device_ip))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка удаления устройства: {e}")
            return False
        finally:
            conn.close()

    def cleanup_old_devices(self, days: int = 30) -> int:
        """Очистить устройства, неактивные более N дней"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            cursor.execute("""
                DELETE FROM user_devices WHERE last_seen < ?
            """, (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка очистки старых устройств: {e}")
            return 0
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя из базы (для сброса trial)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM used_ips WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_devices WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка удаления пользователя {user_id}: {e}")
            return False
        finally:
            conn.close()


db = Database()

