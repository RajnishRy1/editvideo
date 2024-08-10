# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy application files
COPY . .

# Set environment variable for port
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run Flask application
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]