FROM python:3.11-slim

# Atualiza os pacotes e instala curl
RUN apt update && apt install -y curl

# Cria diretório da aplicação
WORKDIR /app

# Copia os arquivos
COPY ../requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

# Expõe a porta do Flask
EXPOSE 8080

# Executa o servidor
CMD ["python", "app.py"]
