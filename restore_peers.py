"""
Скрипт для восстановления всех активных peers из базы данных в WireGuard при перезапуске
Запускается автоматически при старте бота или вручную для восстановления peers

Запуск:
    python3 restore_peers.py
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
        logging.FileHandler('restore_peers.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def restore_active_peers():
    """Восстановить всех активных пользователей в WireGuard из базы данных"""
    
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
            logger.error("❌ SERVER_IP не установлен! Установите переменную окружения или используйте скрипт restore_peers.sh")
            return
    
    logger.info("🔍 Ищу активных пользователей в базе данных...")
    
    # Инициализируем WireGuard менеджер
    wg_manager = WireGuardManager(server_ip, server_public_key)
    
    # Получаем всех пользователей из базы данных
    all_user_ids = db.get_all_users()
    
    if not all_user_ids:
        logger.info("✅ Нет пользователей в базе данных")
        return
    
    logger.info(f"📋 Найдено {len(all_user_ids)} пользователей в базе данных")
    
    restored_count = 0
    skipped_count = 0
    errors_count = 0
    
    for user_id in all_user_ids:
        user = db.get_user(user_id)
        
        if not user:
            continue
        
        # Проверяем активность подписки
        is_active = db.check_user_active(user_id)
        
        if not is_active:
            skipped_count += 1
            continue
        
        public_key = user.get('public_key')
        ip_address = user.get('ip_address')
        
        if not public_key or not ip_address:
            logger.warning(f"⚠️ У пользователя {user_id} нет public_key или ip_address, пропускаю")
            skipped_count += 1
            continue
        
        try:
            expiry_date = datetime.fromisoformat(user['expiry_date']).strftime("%d.%m.%Y")
            logger.info(f"🔍 Восстанавливаю peer для пользователя {user_id} (подписка до {expiry_date})...")
            
            # Добавляем peer на WireGuard сервер
            added = wg_manager.add_peer_to_server(public_key, ip_address)
            
            if added:
                logger.info(f"✅ Peer восстановлен для пользователя {user_id}")
                restored_count += 1
            else:
                logger.warning(f"⚠️ Не удалось полностью восстановить peer для пользователя {user_id}")
                errors_count += 1
                
        except Exception as e:
            logger.error(f"❌ Ошибка при восстановлении peer для пользователя {user_id}: {e}", exc_info=True)
            errors_count += 1
    
    logger.info(f"""
    📊 Итоги восстановления peers:
    ✅ Восстановлено: {restored_count}
    ⏭️ Пропущено (неактивные/нет данных): {skipped_count}
    ⚠️ Ошибок: {errors_count}
    📋 Всего обработано: {len(all_user_ids)}
    """)


if __name__ == "__main__":
    try:
        restore_active_peers()
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

