from flask import Flask, request, jsonify, render_template  # Framework web e utilitários para requisições/respostas
import time                                # Para marcar timestamps e simular uso da região crítica
import os                                  # Para acessar variáveis de ambiente (ex: nome do nó)
import requests                            # Para enviar requisições HTTP para outros nós
import random

# Inicializa a aplicação Flask
app = Flask(__name__)  

# ==================== Variaveis do próprio nó ====================

# Nome do nó atual (definido via variável de ambiente, ex: NODE_NAME=server-1)
node_name = os.getenv("NODE_NAME", "undefined")

# Lista de peers (outros nós do cluster), recebida via variável de ambiente PEERS
# Exemplo: PEERS=server-0,server-1,server-2
peer_list = os.getenv("PEERS", "").split(",")

# ==================== Variaveis do protocolo do cluster sync ====================

# Variáveis de controle de estado (globais)
has_client_request  = False   # Flag que simboliza a existência de um cliente em espera
my_client_timestamp = None    # Timestamp do cliente atual
deferred_replies    = []      # Lista de nós que pediram e foram adiados
ok_counter          = 1       # Contador de oks
ready_to_continue   = False   # Flag para controle de parada do servidor


# ==================== Variaveis do para comunicacao com cluster store ====================
cs_max_nodes = 3

# ==================== Variaveis da web ====================
event_log = []  # Armazena os eventos para mostrar na interface web


# ===================Espera pela inicialização dos servidores do cluster store===================
for i in range(cs_max_nodes):
    cs_final_server = f"db-{i}.db"
    print(f"\n[Conexão inicial] | [{node_name}]: Tentando conexão com servidor [{cs_final_server}]",flush=True)
    
    while True:
        try:
            response = requests.get(f"http://{cs_final_server}:8080/isalive", timeout=1)
            if response.status_code == 200:
                print(f"✅ [{cs_final_server}]: Conexão com [{cs_final_server}] estabelecida!")
                break
        except Exception as e:
            print(f"[Conexão inicial] | [{node_name}] | ⏳ {cs_final_server} ainda não disponível...")

        time.sleep(1)  # Espera 1 segundo antes de tentar de novo


# =================== FUNCOES AUXILIARES ===================

# Função que adiciona um nó na lista de dicionário [timestamp, node] e depois ordena
def add_and_sort(new_request):
    global deferred_replies
    deferred_replies.append(new_request)

    # Ordena a lista com base no timestamp
    deferred_replies.sort(key=lambda x: (x["timestamp"], x["node"]))  # desempata pelo nome do nó

# Função que realiza a requisição da região crítica
def critical_region_request(name, message):
    global cs_max_nodes
    
    attempts          = 0       # Variável que controla quantas tentativas de requisicao ao banco de dados serao feitas. 
    cs_nodes_selected = []      # Lista que armazena quais nós foram tentados
    cs_node_selection = random.randint(0, (cs_max_nodes-1)) # Sorteia uma servidor aleatório para requisitar

    while attempts < 5:
        try:
            # Sorteia outro nó do cluster store para enviar o pedido, caso tenha falhado no pedido anterior 
            while cs_node_selection in cs_nodes_selected:
                cs_node_selection = random.randint(0, (cs_max_nodes-1))
                
            print(f"[critical_region] | [{node_name}] | Conversando com o servidor [db-{cs_node_selection}.db]", flush=True)
            event_log.append(f"[critical_region] | Conversando com o servidor [db-{cs_node_selection}.db]")
            requests.post(f"http://db-{cs_node_selection}.db:8080/write_request", json={"node": name, "value": message}, timeout=1)
            
            # Se deu certo, sai do loop
            print(f"[critical_region] | [{node_name}] | ✅ Utilizou a região crítica!\n", flush=True)
            event_log.append(f"[critical_region] | ✅ Utilizei a região crítica!")
            return True

        # Caso não seja possível comunicar com o pod, tenta conexão com o outro nó do cluster store.
        except requests.exceptions.RequestException:
            print(f"[critical_region: Exception] | [{node_name}] | ❌ Erro: Não foi possível conectar ao servidor [db-{cs_node_selection}.db]", flush=True)
            event_log.append(f"[critical_region: Exception] | ❌ Erro: Não foi possível conectar ao servidor [db-{cs_node_selection}.db]")

            # Adicionando o nó na lista de selecionados
            cs_nodes_selected.append(cs_node_selection)
            
            if len(cs_nodes_selected) >= cs_max_nodes:
                print(f"[critical_region: Exception] | [{node_name}] | ⏳ Nenhum servidor respondeu, aguardando...", flush=True)
                time.sleep(3)
                cs_nodes_selected.clear()
                
            attempts += 1
            
    return False

# def dead_peer_protocol(dead_peer):
#     global peer_list, node_name
    
#     # Remove o peer morto e notifica os demais
#     peer_list.remove(dead_peer)
#     for peer in peer_list:
#         if peer.startswith(node_name): # Não envia para si mesmo
#             continue
#         try:
#             requests.post(f"http://db-{peer}.db:8080/update_peers", json={"dead_peer": dead_peer}, timeout=1)
#         except requests.exceptions.RequestException as e:
#             print(f"[dead_peer_protocol: Exception] | [{node_name}] | ❌ Falha na conexão com {peer}: {e}", flush=True)
#             event_log.append(f"[dead_peer_protocol: Exception] | ❌ Erro: Falha na conexão com {peer}")

#             # dead_peer_protocol(peer)
#     return

def dead_peer_protocol(dead_peer):
    global peer_list, node_name
    
    # Remove o peer morto
    peer_list.remove(dead_peer)
    print(f"[{node_name}] Removendo peer morto: {dead_peer}")
    
    # Coleta todos os peers que falharam na notificação
    failed_peers = []
    peers_to_notify = [p for p in peer_list if not p.startswith(node_name)]
    
    for peer in peers_to_notify:
        try:
            requests.post(f"http://{peer}:8080/update_peers", json={"dead_peer": dead_peer}, timeout=2)
            # print(f"[{node_name}] Notificou {peer} sobre morte de {dead_peer}")
            
        except requests.exceptions.RequestException as e:
            print(f"[dead_peer_protocol: Exception] | [{node_name}] | ❌ Falha na conexão com {peer}: {e}", flush=True)
            event_log.append(f"[dead_peer_protocol: Exception] | ❌ Erro: Falha na conexão com {peer}")
            failed_peers.append(peer)
    
    # Remove todos os peers que falharam
    for failed_peer in failed_peers:
        if failed_peer in peer_list:
            peer_list.remove(failed_peer)
            event_log.append(f"[{node_name}] Removendo peer {failed_peer} (falhou na notificação)")

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================
   
# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200

# @app.route("/attempt", methods=["GET"])
# def attempt():
#     data = request.json                 # Recebimento de dados do cliente
#     my_client_timestamp = data.get("timestamp")    # Obtendo timestamp do cliente
#     client_name         = data.get("client_name")  # Obtendo nome do cliente
#     client_message      = data.get("value")        # Obtendo mensagem do cliente
#     if has_client_request:
#         response = requests.post(f"http://localhost:8080/elect", json={"timestamp": my_client_timestamp, "client_name": client_name, "value":client_message})
#         return response.text, response.status_code
#     else:
#         return "", 400

# Rota chamada por um cliente para iniciar uma tentativa de acesso à região crítica
@app.route("/elect", methods=["POST"])
def elect():
    global has_client_request, peer_list, node_name, my_client_timestamp, ok_counter, deferred_replies, ready_to_continue
    
    has_client_request = True           # Ativação da flag da posse de um cliente
    data = request.json                 # Recebimento de dados do cliente
    my_client_timestamp = data.get("timestamp")    # Obtendo timestamp do cliente
    client_name         = data.get("client_name")  # Obtendo nome do cliente
    client_message      = data.get("value")        # Obtendo mensagem do cliente
    print(f"[Rota elect] | [{node_name}] | 📡 Recebeu pedido do cliente [{client_name}, com timestamp {my_client_timestamp:.4f}", flush=True)
    event_log.append(f"[{time.strftime('%H:%M:%S')}] 📡 Pedido de \"{client_name}\" recebido com timestamp {my_client_timestamp}")
    

    # Para cada nó do cluster sync, enviar um pedido com o timestamp do cliente:
    for peer in peer_list:
        # Não envia solicitação para si mesmo
        if peer.startswith(node_name):
            continue
        
        ready_to_continue = False
        print(f'\n[Rota elect] | [{node_name}] | ⚪️ OK COUNTER (antes de pedir OKs) --> {ok_counter}')
        
        # Envia pedido de acesso à RC
        try:
            print(f'[Rota elect] | [{node_name}] | PEDINDO OK PARA O SERVIDOR: {peer}')
            event_log.append(f"[Rota elect] | PEDINDO OK PARA O SERVIDOR: {peer}")

            peers_response = requests.post(f"http://{peer}:8080/request", json={"timestamp": my_client_timestamp,"node": node_name}, timeout=1)
            # time.sleep(0.1)

            # Se recebeu "OK", sobe o contador de oks
            if peers_response.status_code == 200:  
                ok_counter += 1
                print(f'[Rota elect] | [{node_name}] | 🆗 recebeu OK de {peer} --> {ok_counter}')
                event_log.append(f"[Rota elect] | 🆗 recebi OK de {peer} --> {ok_counter}")
                
            # Se recebeu "WAIT"
            if peers_response.status_code == 202:  
                print(f'[Rota elect] | [{node_name}] | 🛑 Recebeu WAIT de {peer}')
                print(f"[Rota elect] | [{node_name}] | 🕑 Esperando permissão para continuar...", flush=True)
                event_log.append(f"[Rota elect] | 🛑 Recebi WAIT de {peer}. 🕑 Esperando permissão para continuar...")
                while not ready_to_continue:
                    time.sleep(0.1)  # Espera 100ms antes de checar novamente
                    try:
                        # Verifica se o parceiro está vivo
                        requests.get(f"http://{peer}:8080/isalive", timeout=2)
                    except requests.exceptions.RequestException as e:
                        # Se não responder, significa que morreu durante a execução da região crítica e precisa avisar os demais
                        print(f"[Rota elect: WAIT Exception] | [{node_name}] | ❌ Falha na conexão com {peer}: {e}. Iniciando protocolo de peer_morto...", flush=True)  # Caso o peer esteja offline ou com erro
                        event_log.append(f"[Rota elect: WAIT Exception] | ❌ Falha na conexão com {peer}. Iniciando protocolo de peer_morto...")

                        dead_peer_protocol(peer)

        except Exception as e:
            print(f"[Rota elect: Exception] | [{node_name}] | ❌ Falha na conexão com {peer}: {e}", flush=True)  # Caso o peer esteja offline ou com erro
            event_log.append(f"[Rota elect: Exception] | ❌ Falha na conexão com {peer}")
            
            dead_peer_protocol(peer)

            
    # Se recebeu OK de todos os peers (exceto ele mesmo), entra na RC
    if (ok_counter >= len(peer_list)):
        print(f'\n[Rota elect] | [{node_name}] | 🔔 Os {len(peer_list)} OKs foram obtidos! Entrando na RC...')
        event_log.append(f"[Rota elect] | 🔔 Os {len(peer_list)} OKs foram obtidos! Entrando na RC...")
        
        critical_response = critical_region_request(node_name, client_message)
        print(f"[Rota elect] | [{node_name}] | 🔴 saiu da RC\n", flush=True)    
        event_log.append(f"[Rota elect] | 🔴 saí da RC")

    ready_to_continue  = False  # Reset da flag de parada
    has_client_request = False  # Reset da flag de cliente
    ok_counter         = 1      # Reset do contador de oks

    # Para cada nó do cluster que ficou em espera, envia um OK 
    print(f"[Rota elect] | [{node_name}] | 🔓 Liberando os outros nós", flush=True)
    event_log.append(f"[Rota elect] | 🔓 Liberando os outros nós")

    for nodes in deferred_replies:
        print(f"[Rota elect] | [{node_name}] | Liberando nó [{nodes['node']}]", flush=True)
        event_log.append(f"[Rota elect] | Liberando nó [{nodes['node']}]")
        
        requests.post(f'http://{nodes["node"]}.server:8080/release', json={"status": "OK"}, timeout=1)
        # time.sleep(0.1)
    print(f"[Rota elect] | [{node_name}] | 🚀 Nós liberados com sucesso!\n", flush=True)
    event_log.append(f"[Rota elect] | 🚀 Nós liberados com sucesso!")

    # Reset da lista
    deferred_replies.clear() 

    print(f"[Rota elect] | [{node_name}] | ✔️  Mandando a mensagem de commit para o cliente", flush=True)
    event_log.append(f"[Rota elect] | ✔️  Mandando a mensagem de commit para o cliente")

    if critical_response == True:
        return jsonify({"status": "COMITTED"}), 200

    return jsonify({"status": "NOT_COMITTED"}), 500


# Rota que atualiza os peers no caso de um morrer na RC. A rota é chamada quando um nó que recebeu WAIT tenta comunicar com outro e não consegue
@app.route("/update_peers", methods=["POST"])
def update_peers():
    global peer_list, ready_to_continue
    
    data        = request.json          # Extração da mensagem
    dead_peer   = data.get("dead_peer") # Obtendo nome do servidor morto
    
    print(f"\n[Rota update_peers] | [{node_name}] | 🔀 Atualizando nós vivos...", flush=True)
    event_log.append(f"[Rota update_peers] | 🔀 Atualizando nós vivos...")
    
    # Retira o servidor da lista
    peer_list.remove(dead_peer)
    ready_to_continue = True
    return "", 200


# Rota chamada por outros nós do cluster pedindo permissão para acessar a região crítica
@app.route("/request", methods=["POST"])
def on_request():
    global node_name, has_client_request, my_client_timestamp, deferred_replies
    
    # Extrai o JSON enviado pelo outro nó
    message     = request.json                         
    their_ts    = message["timestamp"]
    their_node  = message["node"]
    
    if has_client_request == False: # Caso em que o nó não possui nenhum pedido de cliente
        event_log.append(f"Pedido de {their_node} recebido. O servidor {node_name} não possui cliente. Devolvendo OK...")
        return "", 200


    # Se o timestamp do meu cliente é menor do que o pedido, peça a ele para esperar
    print(f"\n[Rota request] | [{node_name}] | ✅ {their_node} está pedindo OK (ts_dele={their_ts:.4f}) - (ts_meu={my_client_timestamp:.4f}), array:", flush=True)
    print(f'[Rota request] | Lista de pedidos: ANTES --> {deferred_replies}')
    if my_client_timestamp < their_ts:
        print(f"[Rota request] | [{node_name}] | 🔁 [{node_name}] o timestamp do meu cliente é menor", flush=True)
        pending_node = {"timestamp": their_ts, "node": their_node}
        print(f"[Rota request] | [{node_name}] | NÓ PENDENTE: {pending_node}")
        add_and_sort(pending_node)
        print(f'[Rota request] | Lista de pedidos: DEPOIS --> {deferred_replies}\n')
        event_log.append(f"Pedido de {their_node} recebido, com timestamp {their_ts:.4f}. O servidor {node_name} possui timestamp menor: {my_client_timestamp:.4f}. Devolvendo WAIT")
        
        return "", 202
    
    else:
        # Caso contrário, responde com "OK", permitindo o acesso à RC
        print(f"[Rota request] | [{node_name}] ✅ Deu OK para {their_node} (ts={their_ts:.4f})", flush=True)
        print(f'[Rota request] | [{node_name}] | DEPOIS --> {deferred_replies}\n')
        
        event_log.append(f"Pedido de {their_node} recebido, com timestamp {their_ts:.4f}. O servidor {node_name} possui timestamp maior: {my_client_timestamp:.4f}. Devolvendo OK")
        
        return "", 200
    

# Rota chamada para o recebimento de oks de outros nós
@app.route("/release", methods=["POST"])
def release():
    global ok_counter, peer_list, ready_to_continue
    
    # Se a rota foi chamada, aumenta o contador de ok
    ok_counter += 1
    print(f'\n[Rota release] | [{node_name}] | 🔓 Recebeu release, OK COUNT --> {ok_counter} | OKs necessários --> {len(peer_list)}')
    event_log.append(f"🔓 Release recebido. OK COUNT = {ok_counter}, quantidade de OKs necessarios: {len(peer_list)}")
    
    ready_to_continue = True
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
