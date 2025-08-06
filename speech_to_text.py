#!/usr/bin/env python3
"""
Yandex SpeechKit Speech-to-Text проект
Распознавание речи из аудиофайлов с сохранением в текстовый файл
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from pydub import AudioSegment
from typing import Optional, Dict, Any


class YandexSpeechKit:
    """Класс для работы с Yandex SpeechKit API"""
    
    def __init__(self, iam_token: str, folder_id: str):
        self.iam_token = iam_token
        self.folder_id = folder_id
        # Попробуем разные API endpoints
        self.api_urls = [
            "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
            "https://transcribe.api.cloud.yandex.net/speech/v1/stt:recognize", 
            "https://stt.api.cloud.yandex.net/stt/v1/recognize",
            "https://speechkit.api.cloud.yandex.net/speech/v1/stt:recognize"
        ]
        
    def convert_audio_to_supported_format(self, audio_path: str) -> str:
        """Конвертирует аудио в поддерживаемый формат (WAV PCM)"""
        audio = AudioSegment.from_file(audio_path)
        
        # Конвертируем в моно, 16kHz для уменьшения размера файла
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Создаем временный файл в формате WAV с 16-битным кодированием
        output_path = "temp_audio.wav"
        audio.export(output_path, format="wav", parameters=["-acodec", "pcm_s16le"])
        
        return output_path
    
    def recognize_audio(self, audio_path: str, language: str = "ru-RU") -> Dict[str, Any]:
        """Распознает речь из аудиофайла"""
        
        print("🔄 Конвертирую аудио в OGG Opus формат...")
        
        # Конвертируем в OGG Opus
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(48000)
        temp_file = "temp_audio.ogg"
        audio.export(temp_file, format="ogg", codec="libopus")
        
        try:
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            # Проверяем размер файла
            if len(audio_data) > 1024 * 1024:
                raise Exception("Файл слишком большой (>1MB). Уменьшите качество или длительность.")
            
            print(f"📊 Размер OGG файла: {len(audio_data)} байт")
            
            # Правильные заголовки для бинарных данных
            headers = {
                'Authorization': f'Bearer {self.iam_token}',
                'Content-Type': 'audio/ogg',
            }
            
            # Параметры в URL
            params = {
                'topic': 'general',
                'folderId': self.folder_id,
                'lang': language,
                'format': 'oggopus'
            }
            
            print("🚀 Отправляю запрос на распознавание...")
            
            # Отправляем бинарные данные
            response = requests.post(
                self.api_urls[0],
                headers=headers,
                params=params,
                data=audio_data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Ошибка API: {response.status_code} - {response.text}")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _try_multipart_approach(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Подход 1: Multipart/form-data с WAV файлом"""
        print("🔄 Конвертирую в WAV и отправляю как multipart...")
        temp_file = self.convert_audio_to_supported_format(audio_path)
        
        try:
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            if len(audio_data) > 1024 * 1024:
                raise Exception("Файл слишком большой (>1MB)")
            
            print(f"📊 Размер WAV файла: {len(audio_data)} байт")
            
            # Пробуем разные API endpoints
            for i, api_url in enumerate(self.api_urls, 1):
                print(f"🌐 Пробую endpoint {i}: {api_url}")
                
                headers = {'Authorization': f'Bearer {self.iam_token}'}
                
                config = {
                    'specification': {
                        'languageCode': language,
                        'model': 'general',
                        'profanityFilter': False,
                        'partialResults': False,
                        'sampleRateHertz': 16000,
                        'audioEncoding': 'LINEAR16_PCM'
                    }
                }
                
                files = {
                    'config': (None, json.dumps(config), 'application/json'),
                    'audio': ('audio.wav', audio_data, 'audio/wav')
                }
                
                try:
                    response = requests.post(
                        f"{api_url}?folderId={self.folder_id}",
                        headers=headers,
                        files=files,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Успех с endpoint {i}!")
                        return response.json()
                    else:
                        print(f"❌ Endpoint {i} ошибка: {response.status_code} - {response.text[:100]}...")
                        
                except Exception as e:
                    print(f"❌ Endpoint {i} исключение: {e}")
                    continue
            
            raise Exception("Все multipart endpoints не сработали")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _try_ogg_approach(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Подход 2: Конвертация в OGG и отправка как OGG_OPUS"""
        print("🔄 Конвертирую в OGG Opus...")
        
        # Конвертируем в OGG
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(48000)
        temp_file = "temp_audio.ogg"
        audio.export(temp_file, format="ogg", codec="libopus")
        
        try:
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            if len(audio_data) > 1024 * 1024:
                raise Exception("Файл слишком большой (>1MB)")
            
            print(f"📊 Размер OGG файла: {len(audio_data)} байт")
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.iam_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'config': {
                    'specification': {
                        'languageCode': language,
                        'model': 'general',
                        'profanityFilter': False,
                        'partialResults': False,
                        'sampleRateHertz': 48000,
                        'audioEncoding': 'OGG_OPUS'
                    }
                },
                'audio': {
                    'content': audio_base64
                }
            }
            
            response = requests.post(
                f"{self.api_urls[0]}?folderId={self.folder_id}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"OGG ошибка: {response.status_code} - {response.text}")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _try_wav_approach(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Подход 3: WAV с разными параметрами"""
        print("🔄 Пробую WAV с 8kHz...")
        
        # Конвертируем в WAV с 8kHz
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(8000)
        temp_file = "temp_audio_8k.wav"
        audio.export(temp_file, format="wav")
        
        try:
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            if len(audio_data) > 1024 * 1024:
                raise Exception("Файл слишком большой (>1MB)")
            
            print(f"📊 Размер WAV 8kHz файла: {len(audio_data)} байт")
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.iam_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'config': {
                    'specification': {
                        'languageCode': language,
                        'model': 'general',
                        'profanityFilter': False,
                        'partialResults': False,
                        'sampleRateHertz': 8000,
                        'audioEncoding': 'LINEAR16_PCM'
                    }
                },
                'audio': {
                    'content': audio_base64
                }
            }
            
            response = requests.post(
                f"{self.api_urls[0]}?folderId={self.folder_id}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"WAV 8kHz ошибка: {response.status_code} - {response.text}")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def wait_for_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Ожидает завершения асинхронной операции"""
        import time
        
        operation_id = operation.get('id')
        if not operation_id:
            raise Exception("Не получен ID операции")
        
        print(f"⏳ Ожидаю завершения операции {operation_id}...")
        
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
            'Content-Type': 'application/json'
        }
        
        # Проверяем статус операции
        max_attempts = 30  # Максимум 5 минут ожидания
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"https://operation.api.cloud.yandex.net/operations/{operation_id}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    op_status = response.json()
                    
                    if op_status.get('done', False):
                        if 'error' in op_status:
                            raise Exception(f"Ошибка операции: {op_status['error']}")
                        
                        print("✅ Операция завершена успешно!")
                        return op_status.get('response', {})
                    else:
                        print(f"⏳ Операция в процессе... ({attempt + 1}/{max_attempts})")
                        time.sleep(10)  # Ждем 10 секунд
                else:
                    print(f"⚠️ Ошибка проверки статуса: {response.status_code}")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"⚠️ Ошибка при проверке статуса: {e}")
                time.sleep(10)
        
        raise Exception("Превышено время ожидания операции")
    
    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Извлекает текст из ответа API"""
        # Новый API возвращает результат напрямую в поле 'result'
        if 'result' in response:
            if isinstance(response['result'], str):
                return response['result']
            elif isinstance(response['result'], dict) and 'chunks' in response['result']:
                # Старый формат с chunks
                chunks = response['result']['chunks']
                text_parts = []
                
                for chunk in chunks:
                    if 'alternatives' in chunk and chunk['alternatives']:
                        text_parts.append(chunk['alternatives'][0]['text'])
                
                return ' '.join(text_parts)
        
        return ""


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


def main():
    """Основная функция"""
    print("🎤 Yandex SpeechKit - Распознавание речи из аудио")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_env_file()
    
    # Получаем параметры
    if len(sys.argv) < 2:
        print("Использование: python speech_to_text.py <путь_к_аудиофайлу> [язык]")
        print("Пример: python speech_to_text.py audio.ogg ru-RU")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "ru-RU"
    
    # Проверяем существование файла
    if not os.path.exists(audio_path):
        print(f"❌ Файл {audio_path} не найден!")
        sys.exit(1)
    
    # Получаем токен и folder_id
    iam_token = os.getenv('YANDEX_CLOUD_IAM_TOKEN')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    if not iam_token:
        print("❌ Не найден IAM токен! Установите YANDEX_CLOUD_IAM_TOKEN в .env файле")
        sys.exit(1)
    
    if not folder_id:
        print("❌ Не найден Folder ID! Установите YANDEX_FOLDER_ID в .env файле")
        sys.exit(1)
    
    try:
        # Создаем экземпляр SpeechKit
        speechkit = YandexSpeechKit(iam_token, folder_id)
        
        print(f"📁 Обрабатываю файл: {audio_path}")
        print(f"🌍 Язык: {language}")
        
        # Распознаем речь
        response = speechkit.recognize_audio(audio_path, language)
        
        # Извлекаем текст
        recognized_text = speechkit.extract_text_from_response(response)
        
        if recognized_text:
            # Создаем имя выходного файла
            audio_name = Path(audio_path).stem
            output_file = f"output/{audio_name}_transcript.txt"
            
            # Сохраняем результат
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(recognized_text)
            
            print(f"✅ Распознавание завершено!")
            print(f"📝 Результат сохранен в: {output_file}")
            print(f"📄 Распознанный текст:")
            print("-" * 30)
            print(recognized_text)
            print("-" * 30)
            
        else:
            print("⚠️ Текст не был распознан или файл не содержит речи")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()