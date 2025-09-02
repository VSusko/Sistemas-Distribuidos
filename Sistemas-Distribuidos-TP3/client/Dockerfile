# Usa uma imagem oficial do Python 3.11
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner como /app
WORKDIR /app

# Copia o arquivo de dependências 'requirements.txt' da máquina host para o contêiner
COPY ../requirements.txt .

# Instala as dependências de requirements.txt
RUN pip install -r requirements.txt

# Copia o arquivo de aplicação 'app.py'
COPY client.py .

# Executa o client.py com o Python, com a flag -u para que a saída seja exibida sem buffering
CMD ["python", "-u", "client.py"]