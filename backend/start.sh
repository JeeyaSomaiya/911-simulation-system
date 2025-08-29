#!/bin/bash
cd /var/www/ai-call-simulator/backend
source /var/www/ai-call-simulator/backend/venv/bin/activate
exec /var/www/ai-call-simulator/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app
