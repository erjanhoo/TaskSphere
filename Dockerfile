FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала копируем только requirements, чтобы кэшировать слои
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Создаем папку для статики, чтобы не было ошибок прав доступа
RUN mkdir -p /app/staticfiles

EXPOSE 8000

# ВАЖНО: Добавил collectstatic перед запуском
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn TaskSphere.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]