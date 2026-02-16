FROM python:3.11-slim

WORKDIR /app

# System dependencies for OpenCV + InsightFace build
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Remove g++ after build to keep image smaller
RUN apt-get purge -y --auto-remove g++ && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

