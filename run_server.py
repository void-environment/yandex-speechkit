#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера
"""

import uvicorn
import os
from pathlib import Path

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

def check_env():
    """Проверяет переменные окружения"""
    required_vars = ['YANDEX_CLOUD_IAM_TOKEN', 'YANDEX_FOLDER_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Отсутствуют переменные окружения:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n💡 Создайте .env файл с необходимыми переменными")
        return False
    
    return True

def create_directories():
    """Создает необходимые директории"""
    dirs = ['temp/uploads', 'temp/outputs']
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана директория: {dir_path}")

def main():
    """Запуск сервера"""
    print("🚀 Запуск Speech-to-Text микросервиса")
    print("=" * 50)
    
    # Загружаем .env файл
    load_env_file()
    
    # Проверяем окружение
    if not check_env():
        return
    
    # Создаем директории
    create_directories()
    
    print("✅ Все проверки пройдены")
    print("🌐 Запускаю сервер на http://localhost:8002")
    print("📖 Документация API: http://localhost:8002/docs")
    print("🔍 Альтернативная документация: http://localhost:8002/redoc")
    print("\n🛑 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()