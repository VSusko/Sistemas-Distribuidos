FROM python:3.11-slim

WORKDIR /app
COPY app.py .

RUN pip install pymongo

CMD ["python", "-u", "app.py"]