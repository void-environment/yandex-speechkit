"""
API роуты для распознавания речи
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import (
    TranscribeResponse, 
    TaskStatusResponse, 
    ErrorResponse,
    Language,
    TaskStatus
)
from app.services.task_service import task_service
from app.core.config import settings

logger = logging.getLogger("speech_service.api")
router = APIRouter()


def validate_file(file: UploadFile) -> None:
    """Валидация загружаемого файла"""
    
    # Проверяем расширение
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Проверяем размер (если доступен)
    if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимальный размер: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Аудиофайл для распознавания"),
    language: Language = Form(default=Language.RU, description="Язык аудио")
):
    """
    Загружает аудиофайл и создает задачу на распознавание речи
    """
    try:
        # Валидируем файл
        validate_file(file)
        
        # Сохраняем файл
        file_path = await save_uploaded_file(file)
        
        # Создаем задачу
        task_id = task_service.create_task(file_path, language.value)
        
        logger.info(f"Создана задача распознавания {task_id} для файла {file.filename}")
        
        return TranscribeResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Задача создана и поставлена в очередь на обработку"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания задачи: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/transcribe/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Получает статус задачи распознавания
    """
    try:
        task = task_service.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        return TaskStatusResponse(
            task_id=task["id"],
            status=task["status"],
            created_at=task["created_at"],
            completed_at=task["completed_at"],
            result=task["result"],
            error=task["error"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статуса задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/tasks")
async def get_all_tasks():
    """
    Получает список всех задач (для отладки)
    """
    try:
        tasks = task_service.get_all_tasks()
        return {"tasks": list(tasks.values())}
        
    except Exception as e:
        logger.error(f"Ошибка получения списка задач: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


async def save_uploaded_file(file: UploadFile) -> str:
    """
    Сохраняет загруженный файл
    
    Args:
        file: Загруженный файл
        
    Returns:
        Путь к сохраненному файлу
    """
    # Создаем уникальное имя файла
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename).suffix
    
    filename = f"{timestamp}_{unique_id}{file_ext}"
    file_path = Path(settings.UPLOAD_DIR) / filename
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    logger.info(f"Файл сохранен: {file_path}")
    return str(file_path)