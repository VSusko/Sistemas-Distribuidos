FROM python:3.11-slim

# Atualiza os pacotes e instala curl
RUN apt update && apt install -y curl

# Cria diretório da aplicação
WORKDIR /app

# Copia os arquivos de dependências e instala
COPY ../requirements.txt .
RUN pip install -r requirements.txt

# Copia o arquivo principal do app
COPY app.py .

# Copia a pasta templates (HTML)
COPY templates/ templates/

# Copia a pasta static (CSS, JS, imagens)
COPY static/ static/

# Expõe a porta do Flask
EXPOSE 8080

# Executa o servidor
CMD ["python", "app.py"]
