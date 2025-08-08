# Usa imagem leve do Python 3.11
FROM python:3.11-slim

# Atualiza os pacotes e instala o curl (pode ser usado para testes ou verificações HTTP)
RUN apt update && apt install -y curl

# Define o diretório de trabalho como /app
WORKDIR /app

# Copia e instala as dependências do projeto
COPY ../requirements.txt .
RUN pip install -r requirements.txt

# Copia os arquivos da aplicação, incluindo HTMLs e assets
COPY app.py ./
COPY templates ./templates
COPY static/ static/

# Expõe a porta 8080 para acesso externo
EXPOSE 8080

# Executa o aplicativo Python
CMD ["python", "app.py"]