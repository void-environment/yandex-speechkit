"""
Конфигурация приложения
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Yandex Cloud настройки
    YANDEX_CLOUD_IAM_TOKEN: str = ""
    YANDEX_FOLDER_ID: str = ""
    
    # Настройки файлов
    UPLOAD_DIR: str = "temp/uploads"
    OUTPUT_DIR: str = "temp/outputs"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".ogg", ".mp3", ".wav", ".m4a", ".flac"]
    
    # Настройки обработки
    DEFAULT_LANGUAGE: str = "ru-RU"
    CLEANUP_INTERVAL: int = 3600  # Очистка временных файлов каждый час
    FILE_TTL: int = 1800  # Время жизни файлов 30 минут
    
    # Настройки API
    API_TIMEOUT: int = 120  # Таймаут для Yandex API
    MAX_CONCURRENT_REQUESTS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def load_env_file():
    """Загружает переменные окружения из .env файла"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


# Загружаем .env файл
load_env_file()

# Создаем экземпляр настроек
settings = Settings()

# Создаем необходимые директории
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)