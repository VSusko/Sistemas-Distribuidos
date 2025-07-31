from flask import Flask, request, jsonify, render_template  # Framework web e utilitários para requisições/respostas
import time                                # Para marcar timestamps e simular uso da região crítica
import os                                  # Para acessar variáveis de ambiente (ex: nome do nó)
import requests                            # Para enviar requisições HTTP para outros nós

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Nome do nó atual (definido via variável de ambiente, ex: NODE_NAME=server-1)
node_name = os.getenv("NODE_NAME", "undefined")

# Lista de peers (outros nós do cluster), recebida via variável de ambiente PEERS
# Exemplo: PEERS=server-0,server-1,server-2
peer_list = os.getenv("PEERS", "").split(",")

# Variáveis de controle de estado (globais)
has_client_request = False       # Flag que simboliza a existência de um cliente em espera
my_client_timestamp = None       # Timestamp do cliente atual
deferred_replies = []            # Lista de nós que pediram e foram adiados
ok_counter = 1                   # Contador de oks
ready_to_continue = False        # Flag para controle de parada do servidor

# Variaveis da web
event_log = []  # Armazena os eventos para mostrar na interface web

# =================== FUNCOES AUXILIARES ===================

# Função que adiciona um nó na lista de dicionário [timestamp, node] e depois ordena
def add_and_sort(new_request):
    global deferred_replies
    deferred_replies.append(new_request)

    # Ordena a lista com base no timestamp
    deferred_replies.sort(key=lambda x: (x["timestamp"], x["node"]))  # desempata pelo nome do nó

# Função que simula uma entrada na região crítica
def critical_region(timestamp, name):
    critical_response = requests.post(f"http://critical:8080/critical", json={"timestamp": timestamp,"node": name}, timeout=1)
    
    if critical_response.status_code == 200:
        print(f"🟢 [{node_name}] >>> Entrou na região crítica! ✅", flush=True)
        event_log.append(f"{node_name} Entrou na região crítica!")
        time.sleep(3)  # Simula o uso da RC por 3 segundos
    else:
        print(f"❌ [{node_name}] >>> Não foi possível utilizar a região crítica!", flush=True)
    
    return

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota chamada por outros nós do cluster pedindo permissão para acessar a região crítica
@app.route("/request", methods=["POST"])
def on_request():
    global node_name, has_client_request, my_client_timestamp, deferred_replies
    
    # Extrai o JSON enviado pelo outro nó
    message = request.json                         
    their_ts = message["timestamp"]
    their_node = message["node"]
    
    if has_client_request == False: # Caso em que o nó não possui nenhum pedido de cliente
        event_log.append(f"Pedido de {their_node} recebido. O servidor {node_name} não possui cliente. Devolvendo OK...")
        return jsonify({"status": "OK"}), 200


    # Se o timestamp do meu cliente é menor do que o pedido, peça a ele para esperar
    print(f"[Rota request] | [{node_name}] | ✅ {their_node} está pedindo OK (ts_dele={their_ts:.4f}) - (ts_meu={my_client_timestamp:.4f}), array:", flush=True)
    print(f'ANTES --> {deferred_replies}')
    if my_client_timestamp < their_ts:
        print(f"[Rota request] | [{node_name}] | 🔁 [{node_name}] o timestamp do meu cliente é menor", flush=True)
        pending_node = {"timestamp": their_ts, "node": their_node}
        print(f"[Rota request] | [{node_name}] | NÓ PENDENTE: {pending_node}")
        add_and_sort(pending_node)
        print(f'[Rota request] | [{node_name}] | DEPOIS --> {deferred_replies}')
        event_log.append(f"Pedido de {their_node} recebido, com timestamp {their_ts:.4f}. O servidor {node_name} possui timestamp menor: {my_client_timestamp:.4f}. Devolvendo WAIT")
        
        return jsonify({"status": "WAIT"}), 202
    
    else:
        # Caso contrário, responde com "OK", permitindo o acesso à RC
        print(f"✅ [Rota request] | [{node_name}] deu OK para {their_node} (ts={their_ts:.4f})", flush=True)
        print(f'[Rota request] | [{node_name}] | DEPOIS --> {deferred_replies}')
        
        event_log.append(f"Pedido de {their_node} recebido, com timestamp {their_ts:.4f}. O servidor {node_name} possui timestamp maior: {my_client_timestamp:.4f}. Devolvendo OK")
        
        return jsonify({"status": "OK"}), 200
    

# Rota chamada para o recebimento de oks de outros nós
@app.route("/release", methods=["POST"])
def release():
    global ok_counter, peer_list, ready_to_continue
    
    # Se a rota foi chamada, aumenta o contador de ok
    ok_counter += 1
    print(f'\n[Rota release] | [{node_name}] | RECEBI O RELEASE, OK COUNT --> {ok_counter} E QTT NECESSÁRIA --> {len(peer_list)}\n')
    event_log.append(f"Release recebido. OK COUNT = {ok_counter}, quantidade de OKs necessarios: {len(peer_list)}")
    
    ready_to_continue = True
    return "", 200
    

# Rota chamada por um cliente para iniciar uma tentativa de acesso à região crítica
@app.route("/elect", methods=["POST"])
def elect():
    global has_client_request, peer_list, node_name, my_client_timestamp, ok_counter, deferred_replies, ready_to_continue
    
    has_client_request = True           # Ativação da flag da posse de um cliente
    data = request.json                 # Recebimento de dados do cliente
    my_client_timestamp = data.get("timestamp")   # Obtendo timestamp do cliente
    client_name = data.get("client_name")         # Obtendo nome do cliente
    print(f"\n[Rota elect] | [{node_name}] | 📡 recebeu pedido do cliente (ts={my_client_timestamp:.4f}), com nome {client_name}", flush=True)
    
    event_log.append(f"[{time.strftime('%H:%M:%S')}] Pedido de \"{client_name}\" recebido com timestamp {my_client_timestamp}")

    # Para cada nó do cluster sync, enviar um pedido com o timestamp do cliente:
    for peer in peer_list:
        # Não envia solicitação para si mesmo
        if peer.startswith(node_name):
            continue
        
        ready_to_continue = False
        print(f'\n{peer}\n[Rota elect] | [{node_name}] | OK COUNTER (antes de pedir OKs) --> {ok_counter}')
        
        # Envia pedido de acesso à RC
        try:
            print(f'[Rota elect] | [{node_name}] | PEDINDO OK PARA O SERVIDOR: {peer}')
            peers_response = requests.post(f"http://{peer}:8080/request", json={"timestamp": my_client_timestamp,"node": node_name}, timeout=1)
            time.sleep(0.1)

            # Se recebeu "OK", sobe o contador de oks
            if peers_response.status_code == 200:  
                ok_counter += 1
                print(f'[Rota elect] | [{node_name}] | recebeu OK de {peer} --> {ok_counter}')
                event_log.append(f"{node_name} recebeu OK de {peer}")
                
            # Se recebeu "WAIT"
            if peers_response.status_code == 202:  
                print(f'[Rota elect] | [{node_name}] | recebeu WAIT de {peer}')
                print(f"[Rota elect] | [{node_name}] | 🕑 Esperando permissão para continuar...", flush=True)
                event_log.append(f"{node_name} recebeu WAIT de {peer}")
                while not ready_to_continue:
                    time.sleep(0.1)  # Espera 100ms antes de checar novamente

        except Exception as e:
            print(f"[Rota elect] | [{node_name}] | ⚠️ Falha ao contatar {peer}: {e}", flush=True)  # Caso o peer esteja offline ou com erro

    # Se recebeu OK de todos os peers (exceto ele mesmo), entra na RC
    print(f'\n[Rota elect] | [{node_name}] | OK COUNTER --> {ok_counter}')
    critical_region(my_client_timestamp,node_name)
    print(f"[Rota elect] | [{node_name}] | 🔴 saiu da RC", flush=True)


    ready_to_continue = False  # Reset da flag de parada
    has_client_request = False # Reset da flag de cliente
    ok_counter = 0             # Reset do contador de oks

    # Para cada nó do cluster que ficou em espera, envia um OK 
    for nodes in deferred_replies:
        print(f"[Rota elect] | [{node_name}] | Mandando mensagem para o node {nodes['node']}", flush=True)
        requests.post(f'http://{nodes["node"]}.server:8080/release', json={"status": "OK"}, timeout=1)
        time.sleep(0.1)
    # Reset da lista
    deferred_replies.clear() 

    print(f"[Rota elect] | [{node_name}] | 🟢 Mandando a mensagem de commit para o cliente", flush=True)
    return jsonify({"status": "COMMITTED"}), 200
   
# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200


# =================== ROTAS PARA A PAGINA WEB ===================

# Rota para carregar a página web ao iniciar
@app.route('/')
def home():
    return render_template('index.html', node_name=node_name)

# Rota que retorna os últimos logs do servidor
@app.route('/api/logs')
def get_logs():
    return jsonify(event_log[-50:])  # Retorna os últimos 50 eventos 

# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
