"""
Сервис для управления задачами
"""

import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from app.models.schemas import TaskStatus
from app.services.speech_service import YandexSpeechService

logger = logging.getLogger("speech_service.tasks")


class TaskService:
    """Сервис для управления задачами распознавания"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.speech_service = YandexSpeechService()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def create_task(self, audio_path: str, language: str) -> str:
        """
        Создает новую задачу распознавания
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Язык распознавания
            
        Returns:
            ID задачи
        """
        task_id = str(uuid.uuid4())
        
        task_data = {
            "id": task_id,
            "status": TaskStatus.PENDING,
            "audio_path": audio_path,
            "language": language,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.tasks[task_id] = task_data
        
        # Запускаем задачу асинхронно
        asyncio.create_task(self._process_task(task_id))
        
        logger.info(f"Создана задача {task_id} для файла {audio_path}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Получает статус задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Данные задачи или None если не найдена
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict]:
        """Возвращает все задачи"""
        return self.tasks.copy()
    
    async def _process_task(self, task_id: str):
        """
        Обрабатывает задачу распознавания
        
        Args:
            task_id: ID задачи
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Задача {task_id} не найдена")
            return
        
        try:
            # Обновляем статус
            task["status"] = TaskStatus.PROCESSING
            logger.info(f"Начинаю обработку задачи {task_id}")
            
            # Выполняем распознавание
            result = await self.speech_service.transcribe_audio(
                task["audio_path"], 
                task["language"]
            )
            
            # Обновляем результат
            task["status"] = TaskStatus.COMPLETED
            task["result"] = result
            task["completed_at"] = datetime.utcnow()
            
            logger.info(f"Задача {task_id} завершена успешно")
            
        except Exception as e:
            # Обновляем ошибку
            task["status"] = TaskStatus.FAILED
            task["error"] = str(e)
            task["completed_at"] = datetime.utcnow()
            
            logger.error(f"Задача {task_id} завершена с ошибкой: {e}")
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Очищает старые задачи
        
        Args:
            max_age_hours: Максимальный возраст задач в часах
        """
        current_time = datetime.utcnow()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            age = current_time - task["created_at"]
            if age.total_seconds() > max_age_hours * 3600:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.info(f"Удалена старая задача {task_id}")


# Глобальный экземпляр сервиса задач
task_service = TaskService()