import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('GUNICORN_WORKERS', '1'))
worker_class = 'sync'
threads = int(os.getenv('GUNICORN_THREADS', '1'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '60'))
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'debug')
accesslog = '-'
errorlog = '-'
capture_output = True
