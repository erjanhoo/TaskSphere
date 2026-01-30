FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

WORKDIR /app/TaskSphere

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn TaskSphere.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
