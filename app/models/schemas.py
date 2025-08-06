"""
Pydantic модели для API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """Статусы задач"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, Enum):
    """Поддерживаемые языки"""
    RU = "ru-RU"
    EN = "en-US"
    TR = "tr-TR"
    UK = "uk-UA"


class TranscribeRequest(BaseModel):
    """Запрос на распознавание речи"""
    language: Language = Field(default=Language.RU, description="Язык аудио")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "ru-RU"
            }
        }


class TranscribeResponse(BaseModel):
    """Ответ на запрос распознавания"""
    task_id: str = Field(..., description="ID задачи")
    status: TaskStatus = Field(..., description="Статус задачи")
    message: str = Field(..., description="Сообщение")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "12345678-1234-1234-1234-123456789012",
                "status": "pending",
                "message": "Задача создана и поставлена в очередь"
            }
        }


class TaskStatusResponse(BaseModel):
    """Ответ со статусом задачи"""
    task_id: str = Field(..., description="ID задачи")
    status: TaskStatus = Field(..., description="Статус задачи")
    created_at: datetime = Field(..., description="Время создания")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    result: Optional[str] = Field(None, description="Результат распознавания")
    error: Optional[str] = Field(None, description="Ошибка если есть")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "12345678-1234-1234-1234-123456789012",
                "status": "completed",
                "created_at": "2025-01-08T10:00:00Z",
                "completed_at": "2025-01-08T10:00:30Z",
                "result": "Привет, это тестовое сообщение",
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str = Field(..., description="Описание ошибки")
    details: Optional[str] = Field(None, description="Детали ошибки")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Неподдерживаемый формат файла",
                "details": "Поддерживаются только: .ogg, .mp3, .wav, .m4a, .flac"
            }
        }