from flask import Flask, request, jsonify  # Framework web e utilitários para requisições/respostas
import time                                # Para marcar timestamps e simular uso da região crítica

# Inicializa a aplicação Flask
app = Flask(__name__)  

@app.route("/critical", methods=["POST"])
def critical():
    client_data = request.json
    client_name = client_data.get("node")            # Obtendo nome do cliente
    client_timestamp = client_data.get("timestamp")  # Obtendo timestamp do cliente
    current_time = time.time()

    with open('log.txt', 'a') as file:
        file.write("\n ################# \n")
        file.write("\nNode: {client_name}")
        file.write("\nTimestamp: {client_timestamp}")
        file.write("\nArrived at: {current_time}")
        file.write("\n ################# \n")

    print(f"🤑 Acesso à região crítica. Nome do cliente: {client_name}, Timestamp: {client_timestamp}", flush=True)
    return "", 200
    
    
# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
