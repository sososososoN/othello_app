FROM node:24-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend/
COPY static/ ./static/
COPY templates/ ./templates/
COPY content/ ./content/

COPY --from=frontend-builder /frontend/dist ./frontend/dist/

RUN mkdir -p /app/data

EXPOSE 5001

CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "5001"]