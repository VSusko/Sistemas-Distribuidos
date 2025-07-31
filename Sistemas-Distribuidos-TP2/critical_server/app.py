from flask import Flask, request, jsonify, render_template  # Framework web e utilitários para requisições/respostas
from datetime import datetime #Conversor de timestamp para [Data/Mes/Ano Horas:Minutos:Segundos]

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Lista para armazenar os pedidos recebidos
critical_requests = []

# Filtro Jinja2 para formatar timestamp
def timestamp_to_datetime(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    except (TypeError, ValueError) as e:
        print(f"Erro ao converter timestamp: {str(e)}")
        return "Timestamp inválido"

app.jinja_env.filters['timestamp_to_datetime'] = timestamp_to_datetime

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota principal, imprime quem está usando a região crítica e adiciona o nome e o timestamp na lista de pedidos
@app.route("/critical", methods=["POST"])
def critical():
    client_data = request.json                       # Extração da mensagem
    client_name = client_data.get("node")            # Obtendo nome do servidor-cliente
    client_timestamp = client_data.get("timestamp")  # Obtendo timestamp do servidor-cliente

    # Armazena o pedido na lista
    request_entry = {
        "client_name": client_name,
        "timestamp": client_timestamp,
    }
    critical_requests.append(request_entry)

    print(f"🤑 Acesso à região crítica. Nome do cliente: {client_name}, Timestamp: {client_timestamp}")
    
    return jsonify({"status": "success", "message": "Acesso à região crítica concedido!}"}), 200
    
# =================== ROTAS PARA A PAGINA WEB ===================

# Rota chamada na inicialização para renderizar a página com a lista de pedidos
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", requests=critical_requests)

# Rota que retorna os dados dos pedidos em formato JSON para atualização dinâmica
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(critical_requests)

# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
