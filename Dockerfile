FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Рабочая папка для копирования файлов
WORKDIR /app

# 2. Сначала копируем зависимости (они лежат в корне, где и Dockerfile)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 3. Копируем весь проект внутрь /app
COPY . .

# 4. Создаем папку для статики (на всякий случай)
RUN mkdir -p /app/TaskSphere/staticfiles

# 5. ВАЖНЫЙ МОМЕНТ: Заходим внутрь папки с кодом
WORKDIR /app/TaskSphere

EXPOSE 8000

# 6. Запускаем всё, находясь уже внутри папки TaskSphere
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn TaskSphere.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]