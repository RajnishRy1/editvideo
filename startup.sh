#!/bin/bash
apt-get update
apt-get install -y libgl1-mesa-glx libglib2.0-0
gunicorn --bind 0.0.0.0 --workers 2 app:app
