from flask import Flask, request, jsonify, render_template  # Framework web e utilitários para requisições/respostas
import logging
from datetime import datetime

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Lista em memória para armazenar os pedidos recebidos
critical_requests = []

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filtro Jinja2 para formatar timestamp
def timestamp_to_datetime(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    except (TypeError, ValueError) as e:
        logger.error(f"Erro ao converter timestamp: {str(e)}")
        return "Timestamp inválido"

app.jinja_env.filters['timestamp_to_datetime'] = timestamp_to_datetime

@app.route("/critical", methods=["POST"])
def critical():
    client_data = request.json
    client_name = client_data.get("node")            # Obtendo nome do cliente
    client_timestamp = client_data.get("timestamp")  # Obtendo timestamp do cliente

    # Armazena o pedido na lista
    request_entry = {
        "client_name": client_name,
        "timestamp": client_timestamp,
    }
    critical_requests.append(request_entry)

    logger.info(f"🤑 Acesso à região crítica. Nome do cliente: {client_name}, Timestamp: {client_timestamp}")
    
    return jsonify({"status": "success", "message": "Acesso à região crítica concedido!}"}), 200
    
    
@app.route("/", methods=["GET"])
def home():
    # Renderiza a página com a lista de pedidos
    return render_template("index.html", requests=critical_requests)

@app.route("/data", methods=["GET"])
def get_data():
    # Retorna os dados dos pedidos em formato JSON para atualização dinâmica
    return jsonify(critical_requests)


# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
