FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user; uploaded documents go to a volume it owns.
RUN useradd --create-home appuser && mkdir -p /app/data && chown -R appuser /app/data
USER appuser

EXPOSE 8000

# One worker: the local backend keeps its index in memory, so workers would not share it.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
