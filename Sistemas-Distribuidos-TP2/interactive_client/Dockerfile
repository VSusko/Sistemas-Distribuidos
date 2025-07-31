FROM python:3.11-slim

RUN apt update && apt install -y curl

WORKDIR /app

COPY ../requirements.txt .
RUN pip install -r requirements.txt

COPY app.py ./
COPY templates ./templates
COPY static/ static/

EXPOSE 8080

CMD ["python", "app.py"]
