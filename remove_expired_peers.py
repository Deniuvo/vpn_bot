"""
Скрипт для удаления истекших подписок с WireGuard сервера
Удаляет peer с сервера, чтобы VPN перестал работать даже если конфиг установлен на устройстве

Запуск:
    python3 remove_expired_peers.py

Или через cron (каждый день в 3:00):
    0 3 * * * cd /root/vpn_bot && source vpn_env/bin/activate && python3 remove_expired_peers.py >> /root/vpn_bot/expired_peers.log 2>&1
"""
import os
import sys
import logging
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
from wireguard import WireGuardManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expired_peers.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def remove_expired_peers():
    """Найти и удалить всех пользователей с истекшей подпиской"""
    
    # Получаем IP сервера и публичный ключ из переменных окружения
    server_ip = os.getenv("SERVER_IP")
    server_public_key = os.getenv("SERVER_PUBLIC_KEY")
    
    # Если SERVER_IP не установлен, пытаемся определить автоматически
    if not server_ip:
        logger.warning("⚠️ SERVER_IP не установлен в переменных окружения. Пытаюсь определить автоматически...")
        
        # Попытка 1: Получить из WireGuard интерфейса (endpoint)
        try:
            import subprocess
            result = subprocess.run(
                ["wg", "show", "wg0", "endpoints"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                # Извлекаем IP из endpoint (формат: IP:PORT)
                endpoint = result.stdout.strip().split()[0]
                if ':' in endpoint:
                    server_ip = endpoint.split(':')[0]
                    logger.info(f"✅ Определен SERVER_IP из WireGuard: {server_ip}")
        except Exception as e:
            logger.debug(f"Не удалось определить IP из WireGuard: {e}")
        
        # Попытка 2: Получить публичный IP через внешний API
        if not server_ip:
            try:
                import urllib.request
                with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                    server_ip = response.read().decode('utf-8').strip()
                    logger.info(f"✅ Определен SERVER_IP через API: {server_ip}")
            except Exception as e:
                logger.debug(f"Не удалось определить IP через API: {e}")
        
        if not server_ip:
            logger.error("❌ SERVER_IP не установлен! Установите переменную окружения или используйте скрипт remove_expired_peers.sh")
            logger.error("   Пример: export SERVER_IP=\"your_server_ip\"")
            return
    
    logger.info("🔍 Ищу пользователей с истекшей подпиской...")
    
    # Инициализируем WireGuard менеджер
    wg_manager = WireGuardManager(server_ip, server_public_key)
    
    # Получаем список истекших пользователей
    expired_users = db.get_expired_users()
    
    if not expired_users:
        logger.info("✅ Нет пользователей с истекшей подпиской")
        return
    
    logger.info(f"📋 Найдено {len(expired_users)} пользователей с истекшей подпиской")
    
    removed_count = 0
    errors_count = 0
    
    for user in expired_users:
        user_id = user['user_id']
        username = user.get('username', 'unknown')
        expiry_date = user['expiry_date']
        public_key = user.get('public_key')
        ip_address = user.get('ip_address', 'unknown')
        subscription_type = user.get('subscription_type', 'unknown')
        
        try:
            expiry_date_formatted = datetime.fromisoformat(expiry_date).strftime("%d.%m.%Y")
            subscription_info = f"trial (бесплатный)" if subscription_type == 'trial' else subscription_type
            logger.info(f"🔍 Пользователь {user_id} (@{username}): подписка {subscription_info} истекла {expiry_date_formatted}")
            
            if not public_key:
                logger.warning(f"⚠️ У пользователя {user_id} нет public_key, пропускаю")
                # Все равно деактивируем в базе
                db.deactivate_user(user_id)
                continue
            
            # Удаляем peer с WireGuard сервера
            logger.info(f"🗑️ Удаляю peer для пользователя {user_id} (IP: {ip_address})...")
            removed = wg_manager.remove_peer_from_server(public_key)
            
            if removed:
                logger.info(f"✅ Peer удален для пользователя {user_id}")
                removed_count += 1
            else:
                logger.warning(f"⚠️ Не удалось полностью удалить peer для пользователя {user_id}")
                errors_count += 1
            
            # Деактивируем пользователя в базе данных
            db.deactivate_user(user_id)
            logger.info(f"✅ Пользователь {user_id} деактивирован в базе данных")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке пользователя {user_id}: {e}", exc_info=True)
            errors_count += 1
    
    logger.info(f"""
    📊 Итоги удаления истекших подписок:
    ✅ Успешно удалено: {removed_count}
    ⚠️ Ошибок: {errors_count}
    📋 Всего обработано: {len(expired_users)}
    """)


if __name__ == "__main__":
    try:
        remove_expired_peers()
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

