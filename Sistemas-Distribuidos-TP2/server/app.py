from flask import Flask, request, jsonify  # Framework web e utilitários para requisições/respostas
import time                                # Para marcar timestamps e simular uso da região crítica
import os                                  # Para acessar variáveis de ambiente (ex: nome do nó)
import requests                            # Para enviar requisições HTTP para outros nós
import threading                           # Para permitir o congelamento do processo até que receba outros oks

app = Flask(__name__)  # Inicializa a aplicação Flask

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

elect_wait_event = threading.Event()  # Evento que controla quando a rota /elect pode continuar

ready_to_continue = False


# Função que adiciona um nó na lista de dicionário [timestamp, node] e depois ordena
def add_and_sort(new_request):
    global deferred_replies
    deferred_replies.append(new_request)

    # Ordena a lista com base no timestamp
    deferred_replies.sort(key=lambda x: (x["timestamp"], x["node"]))  # desempata pelo nome do nó

# Função que simula uma entrada na região crítica
def critical_region():
    print(f"🟢 [{node_name}] >>> Entrou na região crítica! ✅", flush=True)
    time.sleep(3)  # Simula o uso da RC por 3 segundos


# Rota chamada por outros nós do cluster pedindo permissão para acessar a região crítica
@app.route("/request", methods=["POST"])
def on_request():
    global node_name, has_client_request, my_client_timestamp, deferred_replies
    
    if has_client_request == False: # Caso em que o nó não possui nenhum pedido de cliente
        return jsonify({"status": "OK"}), 200

    # Extrai o JSON enviado pelo outro nó
    message = request.json                         
    their_ts = message["timestamp"]
    their_node = message["node"]

    # Se o timestamp do meu cliente é menor do que o pedido, peça a ele para esperar
    print(f"        ✅ {their_node} está pedindo OK (ts_dele={their_ts:.4f})       (ts_meu={my_client_timestamp:.4f}), array até agora:", flush=True)
    print(f'        ANTES --> {deferred_replies}')
    if my_client_timestamp < their_ts:
        print(f"        🔁 [{node_name}] o timestamp do meu cliente é menor", flush=True)
        pending_node = {"timestamp": their_ts, "node": their_node}
        print("         PENDING NODE:")
        print(f'            {pending_node}')
        add_and_sort(pending_node)
        
        print(f'        DEPOIS --> {deferred_replies}')
        
        return jsonify({"status": "WAIT"}), 202
    
    else:
        # Caso contrário, responde com "OK", permitindo o acesso à RC
        print(f"        ✅ [{node_name}] deu OK para {their_node} (ts={their_ts:.4f})", flush=True)
        
        print(f'        DEPOIS --> {deferred_replies}')
        
        return jsonify({"status": "OK"}), 200
    


@app.route("/release", methods=["POST"])
def release():
    global ok_counter, peer_list, ready_to_continue
    
    ok_counter += 1
    print()
    print(f'RECEBI O RELEASE, OK COUNT --> {ok_counter} E QTT NECESSÁRIA --> {len(peer_list)}')
    print()
    
    # if ok_counter == len(peer_list)-1: # Se o contador de oks chegou ao limite, acorda na rota elect
    #    elect_wait_event.set()  # Sinaliza que todos os OKs foram recebidos
    ready_to_continue = True
    
    print("VOLTA CALABRESO")
    
    return "", 200
    

# Rota chamada por um cliente para iniciar uma tentativa de acesso à região crítica
@app.route("/elect", methods=["POST"])
def elect():
    global has_client_request, peer_list, node_name, my_client_timestamp, ok_counter, deferred_replies, ready_to_continue
    
    has_client_request = True           # Flag de cliente ativada
    data = request.json                 # Recebe dados do cliente
    my_client_timestamp = data.get("timestamp")   # Obtendo timestamp do cliente
    client_name = data.get("client_name")  # Obtendo nomes do cliente
    
    print(f"\n📡 [{node_name}] recebeu pedido do cliente (ts={my_client_timestamp:.4f}), com nome {client_name}", flush=True)
    # print()
    # print(f'A LISTA DE CLIENTES É ESSA --> {peer_list}')
    
    for peer in peer_list:
        # Não envia solicitação para si mesmo
        if peer.startswith(node_name):
            continue
        
        ready_to_continue = False
        
        print()
        print(peer)
        print(f'    OK COUNTER (antes de pedir OKs) --> {ok_counter}')
        try:
            # Envia pedido de acesso à RC para cada peer
            
            print(f'    PEDINDO OK PRA SERVIDOR: {peer}')
            peers_response = requests.post(f"http://{peer}:8080/request", json={"timestamp": my_client_timestamp,"node": node_name}, timeout=1)
            time.sleep(0.1)

            if peers_response.status_code == 200:  # Se recebeu "OK"
                ok_counter += 1
                print(f'    recebeu OK de {peer} --> {ok_counter}')
                
            # if peers_response.status_code == 202:  # Se recebeu "WAIT"
            #     elect_wait_event.wait()  # Aguarda ser acordado pela rota /release

            if peers_response.status_code == 202:  # Se recebeu "WAIT"
                print(f'    recebeu WAIT de {peer}')
                print("     🕑 Esperando permissão para continuar...", flush=True)
                while not ready_to_continue:
                    time.sleep(0.1)  # Espera 100ms antes de checar novamente

                
        except Exception as e:
            print(f"    ⚠️ Falha ao contatar {peer}: {e}", flush=True)  # Caso o peer esteja offline ou com erro

    # Se recebeu OK de todos os peers (exceto ele mesmo), entra na RC
    print()
    print(f'OK COUNTER --> {ok_counter}')
    critical_region()
    print(f"🔴 [{node_name}] saiu da RC", flush=True)
    # elect_wait_event.clear()  # Prepara o evento para a próxima vez
    ready_to_continue = False


    has_client_request = False # Reset da flag
    ok_counter = 0 # Reset do contador de oks

    for nodes in deferred_replies:
        print(f"Mandando mensagem para o node {nodes['node']}", flush=True)
        requests.post(f'http://{nodes["node"]}.server:8080/release', json={"status": "OK"}, timeout=1)
        time.sleep(0.1)
    deferred_replies.clear() # Reset da lista

    print(f"Mandando a mensagem DE COMMIT", flush=True)
    return jsonify({"status": "COMMITTED"}), 200
    
# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
