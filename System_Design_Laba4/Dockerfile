# Используем Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Открываем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["sh", "-c", "python init_db_mongo.py && python init_db_pg.py && uvicorn event_boost:app --host 0.0.0.0 --port 8000"]