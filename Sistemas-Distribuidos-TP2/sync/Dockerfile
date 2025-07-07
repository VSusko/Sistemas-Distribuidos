FROM python:3.10-slim

WORKDIR /app

COPY server.py .

RUN pip install flask
RUN pip install requests

CMD ["python", "server.py"]
