"""
Модуль для работы с WireGuard
Генерация конфигов и управление peers на сервере
"""
import subprocess
import os
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.backends import default_backend
import base64
from typing import Tuple, Optional

CONFIGS_DIR = "configs"
SERVER_PUBLIC_KEY = None  # Будет определен автоматически или настроен
SERVER_IP = None  # Будет определен автоматически или настроен
WG_INTERFACE = "wg0"  # Имя интерфейса WireGuard на сервере


class WireGuardManager:
    def __init__(self, server_ip: str, server_public_key: Optional[str] = None):
        """
        Инициализация менеджера WireGuard
        
        Args:
            server_ip: IP адрес сервера
            server_public_key: Публичный ключ сервера (если не указан, будет считан с сервера)
        """
        global SERVER_IP, SERVER_PUBLIC_KEY
        SERVER_IP = server_ip
        SERVER_PUBLIC_KEY = server_public_key

        # Создаем директорию для конфигов
        if not os.path.exists(CONFIGS_DIR):
            os.makedirs(CONFIGS_DIR)

        # Если публичный ключ не указан, пытаемся получить его с сервера
        if not SERVER_PUBLIC_KEY:
            SERVER_PUBLIC_KEY = self._get_server_public_key()

    def _get_server_public_key(self) -> Optional[str]:
        """
        Получить публичный ключ WireGuard сервера
        Если скрипт запущен на сервере, будет считать ключ
        """
        try:
            # Пытаемся получить публичный ключ через wg команду
            result = subprocess.run(
                ["wg", "show", WG_INTERFACE, "public-key"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Если не удалось получить, возвращаем None
        # В этом случае нужно будет настроить вручную
        return None

    def generate_keypair(self) -> Tuple[str, str]:
        """
        Генерация пары приватный/публичный ключ для клиента
        
        Returns:
            Tuple[приватный_ключ, публичный_ключ]
        """
        # Генерируем приватный ключ
        private_key = X25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Конвертируем в base64 формат WireGuard
        private_bytes = private_key.private_bytes_raw()
        public_bytes = public_key.public_bytes_raw()

        private_key_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_key_b64 = base64.b64encode(public_bytes).decode('utf-8')

        return private_key_b64, public_key_b64

    def create_config(self, user_id: int, private_key: str, ip_address: str,
                     server_public_key: Optional[str] = None) -> str:
        """
        Создание WireGuard конфига для клиента
        
        Args:
            user_id: ID пользователя
            private_key: Приватный ключ клиента
            ip_address: IP адрес клиента (например, 10.0.0.5)
            server_public_key: Публичный ключ сервера (если не указан, используется глобальный)
        
        Returns:
            Путь к созданному файлу конфига
        """
        if not server_public_key:
            server_public_key = SERVER_PUBLIC_KEY

        if not server_public_key:
            raise ValueError("Публичный ключ сервера не установлен. "
                           "Укажите его при инициализации или настройте на сервере.")

        # Используем стандартный порт WireGuard (51820)
        endpoint_port = "51820"
        
        config_content = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_address}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {SERVER_IP}:{endpoint_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

        # Сохраняем конфиг в файл
        config_filename = f"{user_id}.conf"
        config_path = os.path.join(CONFIGS_DIR, config_filename)

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        return config_path

    def add_peer_to_server(self, public_key: str, ip_address: str) -> bool:
        """
        Добавить peer на WireGuard сервер (временно и постоянно)
        
        Args:
            public_key: Публичный ключ клиента
            ip_address: IP адрес клиента
        
        Returns:
            True если успешно добавлен
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Команда для добавления peer на WireGuard сервер (временное изменение)
            # Формат: wg set wg0 peer <public_key> allowed-ips <ip_address>/32
            cmd = [
                "wg", "set", WG_INTERFACE,
                "peer", public_key,
                "allowed-ips", f"{ip_address}/32"
            ]

            logger.info(f"Добавляю peer на сервер: IP={ip_address}, PublicKey={public_key[:20]}...")
            
            # Используем sudo для гарантии прав доступа
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"✅ Peer успешно добавлен временно: IP={ip_address}")
                
                # Проверяем, что peer действительно добавлен
                verify_cmd = ["wg", "show", WG_INTERFACE, "peers"]
                verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=5)
                if public_key in verify_result.stdout:
                    logger.info(f"✅ Peer подтвержден на сервере")
                    
                    # Сохраняем peer в конфиг для постоянства
                    self._save_peer_to_config(public_key, ip_address)
                    
                    return True
                else:
                    logger.warning(f"⚠️ Peer добавлен, но не найден при проверке")
                    # Все равно пытаемся сохранить в конфиг
                    self._save_peer_to_config(public_key, ip_address)
                    return False
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                logger.error(f"❌ Ошибка добавления peer: {error_msg}")
                logger.error(f"   Команда: {' '.join(cmd)}")
                logger.error(f"   Проверьте права доступа - возможно нужен sudo")
                # Пытаемся сохранить в конфиг даже при ошибке временного добавления
                self._save_peer_to_config(public_key, ip_address)
                return False

        except FileNotFoundError:
            logger.error("❌ WireGuard не установлен или команда 'wg' недоступна")
            # Пытаемся сохранить в конфиг
            self._save_peer_to_config(public_key, ip_address)
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при добавлении peer")
            self._save_peer_to_config(public_key, ip_address)
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении peer: {e}", exc_info=True)
            self._save_peer_to_config(public_key, ip_address)
            return False
    
    def _save_peer_to_config(self, public_key: str, ip_address: str) -> bool:
        """
        Сохранить peer в конфигурационный файл WireGuard для постоянства
        
        Args:
            public_key: Публичный ключ клиента
            ip_address: IP адрес клиента
        
        Returns:
            True если успешно сохранен
        """
        import logging
        logger = logging.getLogger(__name__)
        
        config_path = "/etc/wireguard/wg0.conf"
        
        try:
            # Проверяем, существует ли конфиг
            if not os.path.exists(config_path):
                logger.warning(f"⚠️ Конфиг {config_path} не найден, не могу сохранить peer")
                return False
            
            # Читаем конфиг
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Проверяем, нет ли уже этого peer
            if public_key in config_content:
                logger.info(f"✅ Peer уже есть в конфиге")
                return True
            
            # Добавляем peer в конец конфига
            peer_section = f"\n# Peer добавлен автоматически ботом\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {ip_address}/32\n"
            
            # Записываем обратно через sudo (нужны права root)
            try:
                # Используем sudo для записи в системный конфиг
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
                temp_file.write(peer_section)
                temp_file.close()
                
                # Копируем через sudo
                result = subprocess.run(
                    ["sudo", "sh", "-c", f"cat {temp_file.name} >> {config_path}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Удаляем временный файл
                os.unlink(temp_file.name)
                
                if result.returncode == 0:
                    logger.info(f"✅ Peer сохранен в конфиг для постоянства: IP={ip_address}")
                    return True
                else:
                    error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                    logger.warning(f"⚠️ Ошибка записи в конфиг через sudo: {error_msg}")
                    # Пробуем напрямую (может быть уже запущено от root)
                    try:
                        with open(config_path, 'a', encoding='utf-8') as f:
                            f.write(peer_section)
                        logger.info(f"✅ Peer сохранен в конфиг напрямую: IP={ip_address}")
                        return True
                    except PermissionError:
                        logger.warning(f"⚠️ Нет прав для записи в {config_path}. Peer добавлен временно")
                        return False
            except PermissionError:
                logger.warning(f"⚠️ Нет прав для записи в {config_path}. Peer добавлен временно")
                # Пробуем через sudo echo
                try:
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo '# Peer добавлен автоматически ботом' >> {config_path} && echo '[Peer]' >> {config_path} && echo 'PublicKey = {public_key}' >> {config_path} && echo 'AllowedIPs = {ip_address}/32' >> {config_path}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        logger.info(f"✅ Peer сохранен в конфиг через sudo: IP={ip_address}")
                        return True
                except Exception as sudo_error:
                    logger.warning(f"⚠️ Ошибка сохранения через sudo: {sudo_error}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения peer в конфиг: {e}")
            return False

    def remove_peer_from_server(self, public_key: str) -> bool:
        """
        Удалить peer с WireGuard сервера (временно и из конфига)
        
        Args:
            public_key: Публичный ключ клиента для удаления
        
        Returns:
            True если успешно удален
        """
        import logging
        logger = logging.getLogger(__name__)
        
        success = True
        
        try:
            # 1. Удаляем peer временно из работающего WireGuard
            cmd = ["wg", "set", WG_INTERFACE, "peer", public_key, "remove"]
            
            logger.info(f"Удаляю peer с сервера: PublicKey={public_key[:20]}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"✅ Peer удален временно с интерфейса WireGuard")
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                logger.warning(f"⚠️ Ошибка временного удаления peer: {error_msg}")
                # Продолжаем удаление из конфига даже если временное удаление не удалось
            
            # 2. Удаляем peer из конфигурационного файла для постоянства
            config_removed = self._remove_peer_from_config(public_key)
            
            if not config_removed:
                logger.warning(f"⚠️ Не удалось удалить peer из конфига")
                success = False
            
            return success and (result.returncode == 0 or config_removed)

        except Exception as e:
            logger.error(f"❌ Ошибка при удалении peer: {e}")
            # Все равно пытаемся удалить из конфига
            self._remove_peer_from_config(public_key)
            return False
    
    def _remove_peer_from_config(self, public_key: str) -> bool:
        """
        Удалить peer из конфигурационного файла WireGuard
        
        Args:
            public_key: Публичный ключ клиента для удаления
        
        Returns:
            True если успешно удален из конфига
        """
        import logging
        logger = logging.getLogger(__name__)
        
        config_path = "/etc/wireguard/wg0.conf"
        
        try:
            # Проверяем, существует ли конфиг
            if not os.path.exists(config_path):
                logger.warning(f"⚠️ Конфиг {config_path} не найден")
                return False
            
            # Читаем конфиг
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Ищем и удаляем секцию [Peer] с нужным PublicKey
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Если находим начало секции [Peer]
                if line.strip() == "[Peer]":
                    # Читаем всю секцию [Peer] до следующей секции или конца файла
                    peer_section_lines = [line]
                    i += 1
                    
                    # Собираем все строки секции [Peer]
                    while i < len(lines) and not lines[i].strip().startswith("["):
                        peer_section_lines.append(lines[i])
                        i += 1
                    
                    # Проверяем, содержит ли эта секция нужный PublicKey
                    peer_section_content = "".join(peer_section_lines)
                    if public_key in peer_section_content:
                        # Это нужная секция - пропускаем её (не добавляем в new_lines)
                        logger.info(f"✅ Найдена и удалена секция [Peer] с PublicKey={public_key[:20]}...")
                    else:
                        # Это другая секция [Peer] - сохраняем её
                        new_lines.extend(peer_section_lines)
                else:
                    # Обычная строка (не начало секции [Peer]) - сохраняем
                    new_lines.append(line)
                    i += 1
            
            # Записываем обратно (нужны права root)
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                logger.info(f"✅ Peer удален из конфига: {config_path}")
                return True
            except PermissionError:
                logger.error(f"❌ Нет прав для записи в {config_path}. Нужны права root!")
                logger.error(f"   Выполните вручную: sudo python3 remove_expired_peers.py")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления peer из конфига: {e}")
            return False


# Глобальный экземпляр (будет инициализирован в основном файле)
wg_manager = None

