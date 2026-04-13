FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m appuser

USER appuser

COPY . .

EXPOSE 8000

CMD ["python", "-m", "src.api.main"]
