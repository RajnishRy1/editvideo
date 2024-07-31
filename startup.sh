#!/bin/bash
# Update package lists and install required libraries
apt-get update
apt-get install -y ffmpeg

# Run Gunicorn to start your Flask application
# gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app

