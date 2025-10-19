FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY . /app

CMD ["python", "-m", "app.tasks"]
