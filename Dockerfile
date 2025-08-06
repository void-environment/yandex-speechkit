# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as builder

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Продакшн образ
FROM python:3.11-slim

# Устанавливаем только необходимые runtime зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app

# Копируем виртуальное окружение из builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем код приложения
COPY app/ ./app/

# Создаем необходимые директории
RUN mkdir -p temp/uploads temp/outputs && \
    chown -R app:app /app

# Переключаемся на непривилегированного пользователя
USER app

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]