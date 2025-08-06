#!/usr/bin/env python3
"""
FastAPI приложение для микросервиса распознавания речи
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from contextlib import asynccontextmanager

from app.api.routes import transcribe
from app.core.config import settings
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    setup_logging()
    
    # Проверяем конфигурацию при старте
    if not settings.YANDEX_CLOUD_IAM_TOKEN:
        raise RuntimeError("YANDEX_CLOUD_IAM_TOKEN не настроен")
    if not settings.YANDEX_FOLDER_ID:
        raise RuntimeError("YANDEX_FOLDER_ID не настроен")
    
    print("🚀 Speech-to-Text микросервис запущен")
    yield
    # Shutdown
    print("🛑 Speech-to-Text микросервис остановлен")


# Создаем FastAPI приложение
app = FastAPI(
    title="Speech-to-Text Service",
    description="Микросервис для распознавания речи с использованием Yandex SpeechKit",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcribe"])


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Speech-to-Text Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check эндпоинт"""
    return {
        "status": "healthy",
        "service": "speech-to-text",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )