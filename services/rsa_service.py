from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import logging

logger = logging.getLogger(__name__)


class RSAService:
    def __init__(self, keys_dir: str = "./secure_keys"):
        self.keys_dir = keys_dir
        os.makedirs(keys_dir, exist_ok=True, mode=0o700)
        self.private_key_path = os.path.join(keys_dir, "controller_private.pem")
        self.public_key_path = os.path.join(keys_dir, "controller_public.pem")
        self._private_key = None
        self._public_key = None

    def generate_keys(self) -> None:
        """Генерация новой пары RSA-ключей 4096 бит без шифрования"""
        try:
            logger.info("🔐 Генерация новых RSA ключей...")

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )

            # Сохраняем приватный ключ БЕЗ ШИФРОВАНИЯ
            with open(self.private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,  # Более совместимый формат
                    encryption_algorithm=serialization.NoEncryption()
                ))
            os.chmod(self.private_key_path, 0o400)
            logger.info("✅ Приватный RSA ключ сохранен (без шифрования)")

            # Сохраняем публичный ключ
            public_key = private_key.public_key()
            with open(self.public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            os.chmod(self.public_key_path, 0o444)
            logger.info("✅ Публичный RSA ключ сохранен")

        except Exception as e:
            logger.error(f"❌ Ошибка генерации RSA ключей: {e}")
            raise

    def load_keys(self) -> None:
        """Загрузка ключей из файлов"""
        try:
            if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
                logger.warning("RSA ключи не найдены, генерируем новые...")
                self.generate_keys()
                return

            logger.info("🔄 Загрузка существующих RSA ключей...")

            # Загружаем приватный ключ (БЕЗ ПАРОЛЯ)
            with open(self.private_key_path, 'rb') as f:
                private_key_data = f.read()

            self._private_key = serialization.load_pem_private_key(
                private_key_data,
                password=None,  # Важно: без пароля
                backend=default_backend()
            )
            logger.info("✅ Приватный RSA ключ успешно загружен")

            # Загружаем публичный ключ
            with open(self.public_key_path, 'rb') as f:
                public_key_data = f.read()

            self._public_key = serialization.load_pem_public_key(
                public_key_data,
                backend=default_backend()
            )
            logger.info("✅ Публичный RSA ключ успешно загружен")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки RSA ключей: {e}")
            logger.warning("Попытка перегенерировать ключи...")
            self._regenerate_keys()

    def _regenerate_keys(self):
        """Перегенерировать ключи при повреждении"""
        try:
            # Удаляем старые ключи
            for key_file in [self.private_key_path, self.public_key_path]:
                if os.path.exists(key_file):
                    os.remove(key_file)
                    logger.warning(f"Удален поврежденный файл: {key_file}")

            # Генерируем новые ключи
            self.generate_keys()

            # Перезагружаем ключи
            self._private_key = None
            self._public_key = None
            self.load_keys()

            logger.info("✅ RSA ключи успешно перегенерированы")

        except Exception as e:
            logger.error(f"❌ Критическая ошибка перегенерации RSA ключей: {e}")
            raise RuntimeError("Не удалось инициализировать RSA ключи")

    def get_public_key_pem(self) -> str:
        """Получение публичного ключа в PEM формате"""
        if not self._public_key:
            self.load_keys()

        try:
            public_key_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            logger.debug(f"Публичный ключ получен, длина: {len(public_key_pem)} символов")
            return public_key_pem

        except Exception as e:
            logger.error(f"❌ Ошибка получения публичного ключа: {e}")
            raise

    def decrypt_with_private_key(self, encrypted_data: bytes) -> str:
        """Расшифровка данных приватным ключом"""
        if not self._private_key:
            self.load_keys()

        try:
            decrypted = self._private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode('utf-8')

        except Exception as e:
            logger.error(f"❌ Ошибка расшифровки RSA данных: {e}")
            raise ValueError("Не удалось расшифровать данные")

    def ensure_keys_loaded(self):
        """Гарантирует что ключи загружены и валидны"""
        if not self._private_key or not self._public_key:
            self.load_keys()

        # Простая проверка что ключи работают
        try:
            test_data = b"test"
            encrypted = self._public_key.encrypt(
                test_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            decrypted = self.decrypt_with_private_key(encrypted)
            if decrypted == "test":
                logger.info("✅ RSA ключи прошли проверку шифрование/расшифровка")
            return True
        except Exception as e:
            logger.error(f"❌ Проверка RSA ключей не прошла: {e}")
            return False


# Глобальный экземпляр сервиса
rsa_service = RSAService()