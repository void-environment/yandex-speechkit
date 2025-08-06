"""
Сервис для работы с Yandex SpeechKit
"""

import os
import json
import base64
import requests
import logging
from pathlib import Path
from pydub import AudioSegment
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger("speech_service.speech")


class YandexSpeechService:
    """Сервис для работы с Yandex SpeechKit API"""
    
    def __init__(self):
        self.iam_token = settings.YANDEX_CLOUD_IAM_TOKEN
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.api_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        
    async def transcribe_audio(self, audio_path: str, language: str = "ru-RU") -> str:
        """
        Распознает речь из аудиофайла
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Язык распознавания
            
        Returns:
            Распознанный текст
            
        Raises:
            Exception: При ошибке распознавания
        """
        logger.info(f"Начинаю распознавание файла: {audio_path}, язык: {language}")
        
        try:
            # Конвертируем аудио в OGG Opus
            temp_file = await self._convert_to_ogg(audio_path)
            
            try:
                # Читаем конвертированный файл
                with open(temp_file, 'rb') as f:
                    audio_data = f.read()
                
                # Проверяем размер
                if len(audio_data) > settings.MAX_FILE_SIZE:
                    raise Exception(f"Файл слишком большой: {len(audio_data)} байт")
                
                logger.info(f"Размер OGG файла: {len(audio_data)} байт")
                
                # Отправляем запрос к API
                result = await self._send_recognition_request(audio_data, language)
                
                logger.info("Распознавание завершено успешно")
                return result
                
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            raise
    
    async def _convert_to_ogg(self, audio_path: str) -> str:
        """Конвертирует аудио в OGG Opus формат"""
        logger.info("Конвертирую аудио в OGG Opus...")
        
        # Загружаем аудио
        audio = AudioSegment.from_file(audio_path)
        
        # Конвертируем в моно, 48kHz для OGG Opus
        audio = audio.set_channels(1).set_frame_rate(48000)
        
        # Создаем временный файл
        temp_file = f"temp_{datetime.now().timestamp()}.ogg"
        temp_path = Path(settings.UPLOAD_DIR) / temp_file
        
        # Экспортируем в OGG Opus
        audio.export(str(temp_path), format="ogg", codec="libopus")
        
        return str(temp_path)
    
    async def _send_recognition_request(self, audio_data: bytes, language: str) -> str:
        """Отправляет запрос на распознавание к Yandex API"""
        
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
            'Content-Type': 'audio/ogg',
        }
        
        params = {
            'topic': 'general',
            'folderId': self.folder_id,
            'lang': language,
            'format': 'oggopus'
        }
        
        logger.info("Отправляю запрос к Yandex SpeechKit API...")
        
        response = requests.post(
            self.api_url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=settings.API_TIMEOUT
        )
        
        if response.status_code != 200:
            error_msg = f"API ошибка: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Парсим ответ
        result = response.json()
        text = self._extract_text_from_response(result)
        
        if not text:
            raise Exception("Не удалось распознать речь в файле")
        
        return text
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Извлекает текст из ответа API"""
        
        # Новый API возвращает результат в поле 'result'
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