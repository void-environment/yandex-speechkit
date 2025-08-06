#!/usr/bin/env python3
"""
Быстрый запуск проекта Yandex SpeechKit
Проверяет настройки и запускает распознавание
"""

import os
import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Проверяет установленные зависимости"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import pydub
        import requests
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        return False


def check_env_file():
    """Проверяет файл .env"""
    print("🔍 Проверка файла .env...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден")
        print("💡 Скопируйте .env.example в .env и заполните токены")
        return False
    
    # Загружаем переменные
    env_vars = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Проверяем токены
    iam_token = env_vars.get('YANDEX_CLOUD_IAM_TOKEN', '')
    folder_id = env_vars.get('YANDEX_FOLDER_ID', '')
    
    if not iam_token or iam_token == 'your_real_iam_token_here':
        print("❌ IAM токен не настроен")
        return False
    
    if not folder_id or folder_id == 'your_real_folder_id_here':
        print("❌ Folder ID не настроен")
        return False
    
    print("✅ Файл .env настроен корректно")
    return True


def check_yc_cli():
    """Проверяет Yandex Cloud CLI"""
    print("🔍 Проверка Yandex Cloud CLI...")
    
    yc_paths = [
        '~/yandex-cloud/bin/yc',
        'yc'
    ]
    
    for yc_path in yc_paths:
        try:
            result = subprocess.run([os.path.expanduser(yc_path), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Yandex Cloud CLI найден: {yc_path}")
                return yc_path
        except:
            continue
    
    print("⚠️ Yandex Cloud CLI не найден")
    print("💡 Установите CLI для получения токенов:")
    print("   curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash")
    return None


def get_tokens_interactive(yc_path):
    """Интерактивное получение токенов"""
    print("\n🔑 Получение токенов...")
    
    try:
        # Получаем IAM токен
        print("📝 Получаю IAM токен...")
        result = subprocess.run([os.path.expanduser(yc_path), 'iam', 'create-token'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            iam_token = result.stdout.strip()
            print("✅ IAM токен получен")
        else:
            print(f"❌ Ошибка получения IAM токена: {result.stderr}")
            return None, None
        
        # Получаем Folder ID
        print("📝 Получаю список папок...")
        result = subprocess.run([os.path.expanduser(yc_path), 'resource-manager', 'folder', 'list'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Есть заголовок и хотя бы одна папка
                # Берем первую папку (обычно default)
                folder_line = lines[1].split()
                if len(folder_line) > 0:
                    folder_id = folder_line[0]
                    print(f"✅ Folder ID получен: {folder_id}")
                    return iam_token, folder_id
        
        print(f"❌ Ошибка получения Folder ID: {result.stderr}")
        return iam_token, None
        
    except Exception as e:
        print(f"❌ Ошибка получения токенов: {e}")
        return None, None


def update_env_file(iam_token, folder_id):
    """Обновляет файл .env с новыми токенами"""
    print("📝 Обновляю файл .env...")
    
    env_content = f"""# Yandex Cloud настройки
YANDEX_CLOUD_IAM_TOKEN={iam_token}
YANDEX_FOLDER_ID={folder_id}

# Для JWT аутентификации (опционально)
SERVICE_ACCOUNT_ID=your_service_account_id
YANDEX_KEY_ID=your_key_id
YANDEX_PRIVATE_KEY=your_private_key_here
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env обновлен")


def test_audio_recognition():
    """Тестирует распознавание аудио"""
    print("\n🎤 Тестирование распознавания...")
    
    audio_file = "audio_2025-08-06_11-31-35.ogg"
    
    if not os.path.exists(audio_file):
        print(f"❌ Тестовый аудиофайл {audio_file} не найден")
        return False
    
    try:
        # Запускаем простой скрипт
        result = subprocess.run([sys.executable, 'speech_to_text.py', audio_file], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Тест распознавания прошел успешно!")
            print("📄 Результат:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Ошибка тестирования: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запуска теста: {e}")
        return False


def main():
    """Основная функция быстрого запуска"""
    print("🚀 Быстрый запуск Yandex SpeechKit проекта")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        return
    
    # Проверяем .env файл
    env_ok = check_env_file()
    
    # Если .env не настроен, пытаемся получить токены
    if not env_ok:
        yc_path = check_yc_cli()
        if yc_path:
            print("\n💡 Попытка автоматического получения токенов...")
            iam_token, folder_id = get_tokens_interactive(yc_path)
            
            if iam_token and folder_id:
                update_env_file(iam_token, folder_id)
                env_ok = True
            else:
                print("\n❌ Не удалось получить токены автоматически")
                print("📋 Выполните настройку вручную:")
                print("   1. ~/yandex-cloud/bin/yc init")
                print("   2. ~/yandex-cloud/bin/yc iam create-token")
                print("   3. ~/yandex-cloud/bin/yc resource-manager folder list")
                print("   4. Обновите .env файл")
                return
    
    if env_ok:
        # Тестируем распознавание
        if test_audio_recognition():
            print("\n🎉 Проект готов к работе!")
            print("\n📖 Примеры использования:")
            print("   python speech_to_text.py audio.ogg")
            print("   python main.py --audio *.mp3 --output-dir results/")
        else:
            print("\n⚠️ Проект настроен, но тест не прошел")
            print("💡 Проверьте токены и попробуйте еще раз")


if __name__ == "__main__":
    main()