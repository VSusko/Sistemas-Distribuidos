from flask import Flask, request, jsonify, render_template  # Framework web e utilitários para requisições/respostas
from datetime import datetime #Conversor de timestamp para [Data/Mes/Ano Horas:Minutos:Segundos]
import requests
import random
import time


# Inicializa a aplicação Flask
app = Flask(__name__)  

# Lista para armazenar os pedidos recebidos
critical_requests = []
version = 1
value = None

# Filtro Jinja2 para formatar timestamp
def timestamp_to_datetime(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    except (TypeError, ValueError) as e:
        print(f"Erro ao converter timestamp: {str(e)}", flush=True)
        return "Timestamp inválido"

# app.jinja_env.filters['timestamp_to_datetime'] = timestamp_to_datetime

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota principal, imprime quem está usando a região crítica e adiciona o nome e o timestamp na lista de pedidos
@app.route("/write", methods=["POST"])
def write():
    client_data = request.json                       # Extração da mensagem
    client_name = client_data.get("client_name")     # Obtendo nome do cliente
    server_name = client_data.get("server_name")     # Obtendo nome do servidor

    print(f"🤑 Acesso à região crítica. Nome do cliente: {client_name}, Nome do servidor: {server_name}", flush=True)
    
    choosed_one = None
    for i in range (3, 5):
        choosed_one = f"db{i}"
        try:
            resp = requests.post(f"http://{choosed_one}/refresh", json={"version": version+1, "value": random.randint(1,1000)}, timeout=1)
            if resp.status_code == 400:
                print(f"Erro no db{i}", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"Falha ao contactar {choosed_one}: {e}", flush=True)
    
    critical_requests.append({
        "client_name": client_name,
        "server_name": server_name,
        "timestamp": time.time()
    })

    return jsonify({"status": "success", "message": "Acesso à região crítica concedido!"}), 200



@app.route("/refresh", methods=["POST"])
def refresh():
    global version, value
    
    data = request.json                       # Extração da mensagem
    version_ = data.get("version")     # Obtendo nome do servidor-cliente
    value_ = data.get("value")     # Obtendo nome do servidor-cliente
    
    # Atualização
    version = version_
    value = value_
    
    print(f"Valores atualizados", flush=True)
    
    return jsonify({"status": "success", "message": "Acesso à região crítica concedido!}"}), 200


# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200


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
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)
