from flask import Flask, request, render_template, jsonify # Framework web e utilitários para requisições/respostas
import os                        # Para acessar variáveis de ambiente (ex: nome do nó)
import requests

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Nome do nó atual (definido via variável de ambiente, ex: NODE_NAME=db-1)
node_name = os.getenv("NODE_NAME", "undefined") + ".db"

# Lista dos nós primarios
primary_nodes = [None] * 3

# Lista das flags dos primarios
is_primary = [None] * 3

# Definição dos nós primarios: indice 0 = create, indice 1 = append, indice 2 = delete
if node_name == "db-0.db":
    is_primary[0] = True
else:
    is_primary[0] = False

if node_name == "db-1.db":
    is_primary[1] = True
else:
    is_primary[1] = False

if node_name == "db-2.db":
    is_primary[2] = True
else:
    is_primary[2] = False
    
# Nome do servidor primario do cluster store
primary_nodes[0] = "db-0.db"
primary_nodes[1] = "db-1.db"
primary_nodes[2] = "db-2.db"

# Lista de peers (outros nós do cluster store), recebida via variável de ambiente PEERS
# Exemplo: PEERS=db-0,db-1,db-2
peer_list = os.getenv("PEERS", "").split(",")

# Inicializando lista para armazenar as informações dos clientes
clients_database = [""] * 5

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200

# Rota que atende as requisições de escrita do cliente
@app.route("/write_request", methods=["POST"])
def write_request():
    global node_name, peer_list, primary_nodes, is_primary
    
    # Obtendo dados do cliente
    data        = request.json        # Extração da mensagem
    client_name = data.get("node")    # Obtendo nome do servidor-cliente
    message     = data.get("value")   # Obtendo mensagem nova
    client_number = int(client_name.split("-")[-1]) # Obtendo a posição do cliente no banco
    instruction   = message[7:]
    true_message  = clients_database[client_number]
    
    print(f"[Rota write_request] | [{node_name}] | 🟡 Recebeu pedido do cliente [{client_name}] | Atual estado do banco: '{clients_database[client_number]}'. Chamando primário...", flush=True)
    
    # R1
    # Se quem recebeu o pedido foi o próprio primario, manda a rota para ele mesmo
    if message.startswith("create"):
        print(f"[Rota write_request] | [{node_name}] | Operação = create")
        
        true_message = instruction
        primary   = primary_nodes[0]
        operation = "create"
    
    elif message.startswith("append"):
        print(f"[Rota write_request] | [{node_name}] | Operação = append")
        
        true_message = clients_database[client_number] + instruction
        primary   = primary_nodes[1]
        operation = "append"
    
    elif message.startswith("delete"):
        print(f"[Rota write_request] | [{node_name}] | Operação = delete")
        
        if instruction != "" or clients_database[client_number].find(instruction) != -1:
            true_message = clients_database[client_number].replace(f"{instruction}", "")
        else:
            print(f"pra remover só a última letra {clients_database[client_number][-1]}",flush=True)
            true_message = clients_database[client_number] - clients_database[client_number][-1]
        primary   = primary_nodes[2]
        operation = "delete"
    
    else:
        print("Não começa com nenhum dos 3 prefixos...", flush=True)
        return jsonify({"status": "NOT_COMMITED"}), 500
    
    success = False
    while not success:    
        try:
            requests.post(f"http://{primary}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
            print(f"[Rota write_request] | [{node_name}] |🟢 Recebeu confirmação do servidor principal'\n", flush=True)
            success = True

        # Caso o primário tenha não responda, elege um novo
        except requests.exceptions.RequestException as e: 
            print(f"[Rota write_request: Exception] | [{node_name}] | ❌ Erro {e} na conexão com o primário {primary} da operação '{operation}'. Convocando eleição...", flush=True)
            
            # Envia o pedido de eleição para todos os outros nós que não são o primario. A lista é atualizada na eleicao, por isso, o primario antigo nunca eh chamado
            for peer in peer_list:
                try:
                    requests.get(f"http://{peer}:8080/elect_new_primary/{operation}", timeout=1)
                except requests.exceptions.RequestException:
                    print(f"[Rota write_request: Exception Exception] | [{node_name}] | ❌ Erro {e} ao falar com o servidor {peer}", flush=True)
                    
            print(f"[Rota write_request] | ⚙️ Operação de eleição terminada. Lista de peers atual --> {peer_list}", flush=True)
    
    return jsonify({"status": "COMMITED"}), 200


# Rota ativada somente no servidor primário. Controla a escrita do banco dentro dele mesmo e faz o pedido de escrita nos demais servidores
@app.route("/write_primary", methods=["POST"])
def write_primary():
    global node_name, peer_list
    
    # Obtendo dados do cliente
    data             = request.json                 # Extração da mensagem
    client_name      = data.get("client_name")      # Obtendo nome do cliente
    new_value        = data.get("value")            # Obtendo mensagem do cliente
    client_number    = int(client_name.split("-")[-1]) # Obtendo a posição do cliente no banco

    print(f"[Rota write_primary] | [{node_name}] | 🤑 Acesso à região crítica", flush=True)
    print(f"[Rota write_primary] | [{node_name}] | Cliente: [{client_name}] | Estado atual do banco: '{clients_database[client_number]}'", flush=True)

    # Atualizando o banco do cliente
    clients_database[client_number] = new_value

    print(f"[Rota write_primary] | [{node_name}] | 📝 Atualização das informações do cliente! | Novo estado do banco: '{clients_database[client_number]}'", flush=True)
        
    # Para cada peer, faz a solicitação da escrita no banco deles
    for peer in peer_list:
        # Não manda para si próprio
        if peer == node_name:
            continue
        print(f"[Rota write_primary] | [{node_name}] | 🔄 Enviando pedido de atualização para o {peer}", flush=True)
        
        # Tenta pedir ao outro nó que atualize         
        try:
            requests.post(f"http://{peer}:8080/refresh_database", json={"name": client_name, "value": new_value}, timeout=1)

        # Caso não seja possível comunicar com o nó, avisa os demais nós que ele caiu 
        except requests.exceptions.RequestException as e: 
            print(f"[Rota write_primary: Rerfesh Exception] | {node_name} | ❌ Erro {e} na conexão com o servidor {peer}",flush=True)
            for other_peers in peer_list:
                # Não envia para o peer cuja conexão falhou
                if other_peers == peer:
                    continue
                try:
                    print(f"[Rota write_primary: Refresh Exception] | [{node_name}] | ⚠️ Notificando peer {other_peers} da inanição de {peer}", flush=True)
                    requests.post(f"http://{other_peers}:8080/update_peers", json={"dead_peer": peer}, timeout=1)

                except requests.exceptions.RequestException:
                    print(f"[Rota write_primary: Rerfesh Exception Exception] | {node_name} | ❌ Erro {e} na conexão com o servidor {other_peers}", flush=True)
    print(f"",flush=True)
        
    return "", 200


@app.route("/elect_new_primary/<operation>", methods=["GET"])
def elect_new_primary(operation):
    global is_primary, peer_list, primary_nodes

    # Mapeia operação → índice no vetor
    operation_index = {"create": 0, "append": 1, "delete": 2}
    
    # A partir do mapa, obtem o indice do novo primario
    new_primary_index = operation_index[operation]
    old_primary = primary_nodes[new_primary_index]

    print(f"\n[Rota elect_new_primary] | [{node_name}] | 👑 Eleição para {operation}!", flush=True)
    print(f"[Rota elect_new_primary] | [{node_name}] | Nome do removido --> {old_primary}", flush=True)

    # Remove o primário da lista
    if old_primary in peer_list:
        peer_list.remove(old_primary)

    # O novo primário é sempre o de maior número
    new_primary = f"db-{len(peer_list)-1}.db"
    primary_nodes[new_primary_index] = new_primary

    # Se o primário for o próprio nó, ativa a flag
    if new_primary == node_name:
        print(f"[Rota elect_new_primary] | [{node_name}] | Sou o novo primário de {operation}.\n", flush=True)
        is_primary[new_primary_index] = True

    return "", 200


# Rota que atualiza os peers no caso de um não primário falhar. A rota é chamada quando um primário tenta comunicar com outro e não consegue
@app.route("/update_peers", methods=["POST"])
def update_peers():
    global peer_list
    
    data        = request.json          # Extração da mensagem
    dead_peer   = data.get("dead_peer") # Obtendo nome do servidor morto
    
    print(f"\n[Rota update_peers] | [{node_name}] | 🔀 Atualizando nós vivos...", flush=True)
    # Retira o servidor da lista
    peer_list.remove(dead_peer)
    return "", 200

# Rota que atualiza o banco de dados de um determinado cliente. A rota é chamada quando um primário recebe a requisição e repassa aos demais nós
@app.route("/refresh_database", methods=["POST"])
def refresh_database():
    global clients_database
    
    # Obtendo informações do cliente 
    data        = request.json        # Extração da mensagem
    client_name = data.get("name")    # Obtendo nome do servidor-cliente
    new_value   = data.get("value")   # Obtendo nome do servidor-cliente
    client_number = int(client_name.split("-")[-1]) # Obtendo a posição do cliente no banco
    
    print(f"[Rota refresh_database] | [{node_name}] |📩 Recebeu pedido de atualização do servidor primário | Cliente [{client_name}] | Estado do banco: '{clients_database[client_number]}'", flush=True)
    # Escreve o novo valor no banco
    clients_database[client_number] = new_value
    
    print(f"[Rota refresh_database] | [{node_name}] |📝 Cliente [{client_name}] atualizado! | Estado do banco: '{clients_database[client_number]}'\n", flush=True)
    
    return "", 200

# =================== ROTAS PARA A INTERFACE WEB ===================

@app.route("/")
def index():
    return render_template(
        "index.html",
        clients_database=clients_database,
        node_name=node_name,
        primary_node_create=primary_nodes[0],
        primary_node_update=primary_nodes[1],
        primary_node_delete=primary_nodes[2],
        is_primary_create=is_primary[0],
        is_primary_update=is_primary[1],
        is_primary_delete=is_primary[2]
    )


# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)