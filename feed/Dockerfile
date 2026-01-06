FROM python:3.9

ENV PYTHONUNBUFFERED 1
WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
  apt-get install -y --no-install-recommends libpq-dev && \
  rm -rf /var/lib/apt/lists/* && \
  pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED true
CMD ["python", "main.py"]
