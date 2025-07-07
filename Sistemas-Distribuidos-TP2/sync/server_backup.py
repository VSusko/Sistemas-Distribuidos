from flask import Flask, request, jsonify  # Importa os módulos do Flask necessários:
                                           # - Flask: para criar o servidor web
                                           # - request: para acessar dados da requisição
                                           # - jsonify: para retornar respostas no formato JSON
import socket
import requests
import time

DEBUG = 1
TOTAL_NODES_CLUSTER_SYNC = 5


class Cluster_member:
    def __init__(self):
        self.name = socket.gethostname()  

    def cluster_synchronize(self, message):
        for i in range(TOTAL_NODES_CLUSTER_SYNC): # Enviando mensganes aos nós do cluster
            self.send_message_to_cluster_nodes(f'sync{i}', message)
            
        for i in range(TOTAL_NODES_CLUSTER_SYNC): # Recebendo mensganes dos outros nós
            self.recieve_from_cluster(i)
        
        for i in range(TOTAL_NODES_CLUSTER_SYNC):
            print(self.timestamps_array[i])
            
            
    def send_message_to_cluster_nodes(self, destiny, message):
        try:
            response = requests.post(f'http://sync{destiny}:5000/acesso', json=message)
            print(f"Resposta de {destiny}: {response.status_code}")
        except Exception as e:
            print(f"Erro ao comunicar com {destiny}: {e}")
            
    def recieve_from_cluster(self, index):
        response = request.get_json()
        self.timestamps_array[index] = {"sync_id":response["sync_id"], "timestamp":response["timestamp"], "request":response["request"]}

app = Flask(__name__)  # Cria a aplicação Flask. O argumento __name__ informa ao Flask onde ele está sendo executado.

@app.route('/acesso', methods=['POST'])  # Define a rota "/acesso", que aceita apenas requisições POST
def acesso():
    client_message = request.get_json()  # Extrai o corpo da requisição como JSON (espera que o cliente envie um JSON válido)
    
    if DEBUG:
        print(f"Recebido: {client_message}")  # Imprime no terminal os dados recebidos (útil para debug ou log)
    
    first_key = list(client_message.keys())[0]
    
    if first_key == "client_id": # O primeiro campo é client_id
        if DEBUG:
            print("O primeiro campo é client_id")
        
        new_message = {
            "sync_id": socket.gethostname(),            # ID do sync
            "timestamp": client_message["timestamp"],   # Tempo atual (para ordenação)
            "request": "WRITE"                          # Tipo de requisição (escrita)
        }
        
        sync.cluster_synchronize(new_message)
        
    elif first_key == "sync_id": # O primeiro campo é sync_id
        if DEBUG:
            print("O primeiro campo é sync_id")
        
        new_message = {
            "sync_id": socket.gethostname(),            # ID do sync
            "timestamp": "null",   # Tempo atual (para ordenação)
            "request": "OK"                          # Tipo de requisição (escrita)
        }

    else: # O primeiro campo é outro
        if DEBUG:
            print(f"O primeiro campo é outro: {first_key}")

    return jsonify({"status": "COMMITTED"}), 200  # Retorna uma resposta JSON com status 200 (sucesso)
                                                  # {"status": "COMMITTED"} simula a resposta de autorização de escrita

if __name__ == "__main__":  # Garante que este código só execute se o arquivo for rodado diretamente
    sync = Cluster_member()
    app.run(host="0.0.0.0", port=5000)  # Inicia o servidor Flask na porta 5000
                                        # host="0.0.0.0" permite acesso externo (ex: de outros containers)
