#!/bin/bash
# Update package lists and install required libraries
apt-get update
apt-get install -y libgl1-mesa-glx libglib2.0-0

# Run Gunicorn to start your Flask application
gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
