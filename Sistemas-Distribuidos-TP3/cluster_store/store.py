from flask import Flask, request, render_template, jsonify # Framework web e utilitários para requisições/respostas
import os       # Para acessar variáveis de ambiente (ex: nome do nó)
import requests # Para enviar requisições HTTP para outros nós

# ==================== Variaveis do próprio nó ====================

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Nome do nó atual (definido via variável de ambiente, ex: NODE_NAME=db-1)
node_name = os.getenv("NODE_NAME", "undefined") + ".db"

# ==================== Variaveis do protocolo do cluster store ====================
# Lista dos nós primarios
primary_nodes = [None] * 3
# Lista das flags dos primarios
is_primary = [None] * 3

# Definição dos nós primarios: indice 0 = create, indice 1 = append, indice 2 = delete
if node_name == "db-0.db": # O servidor 0 começa como primário da operação "create"
    is_primary[0] = True
else:
    is_primary[0] = False

if node_name == "db-1.db": # O servidor 1 começa como primário da operação "append"
    is_primary[1] = True
else:
    is_primary[1] = False

if node_name == "db-2.db": # O servidor 2 começa como primário da operação "delete"
    is_primary[2] = True
else:
    is_primary[2] = False
    
# Nome do servidor primário do cluster store
primary_nodes[0] = "db-0.db" # Primário de create = servidor 0
primary_nodes[1] = "db-1.db" # Primário de append = servidor 1
primary_nodes[2] = "db-2.db" # Primário de delete = servidor 2

# Lista de peers (outros nós do cluster store), recebida via variável de ambiente PEERS
# Exemplo: PEERS=db-0,db-1,db-2
peer_list = os.getenv("PEERS", "").split(",")

print(f"[{node_name}] | Lista de peers --> {peer_list}", flush=True)

# Lista que representa o banco de dados dos clientes
clients_database = [""] * 5

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota que atende as requisições de escrita do servidor-cliente. Recebe o nome do cliente e a mensagem que será decodificada
@app.route("/write_request", methods=["POST"])
def write_request():
    global node_name, peer_list, primary_nodes, is_primary
    
    # Obtendo dados do cliente
    data            = request.json        # Extração da mensagem
    client_name     = data.get("node")    # Obtendo nome do cliente
    whole_message   = data.get("value")   # Obtendo mensagem completa enviada na request
    client_number   = int(client_name.split("-")[-1]) # Obtendo a posição do cliente no banco
    instruction     = whole_message[7:]  # Obtendo a string depois do comando
    new_client_string  = clients_database[client_number] # String que será manipulada pelas operações. Começa como sendo a última modificação no banco de dados
    
    print(f"[Rota write_request] | [{node_name}] | 🟡 Recebeu pedido do cliente [{client_name}] | Atual estado do banco: '{clients_database[client_number]}'. Chamando primário...", flush=True)
    
    # Se o comando for create:
    if whole_message.startswith("create"):
        print(f"[Rota write_request] | [{node_name}] | Operação = create")
        
        new_client_string = instruction # Apenas troca a nova string pela antiga
        operation = 0 # Operação 0 = create
    
    # Se o comando for append:
    elif whole_message.startswith("append"):
        print(f"[Rota write_request] | [{node_name}] | Operação = append")
        
        new_client_string = clients_database[client_number] + instruction # Concatena a string nova ao final
        operation = 1 # Operação 0 = append
    
    # Se o comando for append: delete
    elif whole_message.startswith("delete"):
        print(f"[Rota write_request] | [{node_name}] | Operação = delete")
        
        # Retira da string antiga a substring enviada pelo cliente
        new_client_string = clients_database[client_number].replace(f"{instruction}", "")
        operation = 2 # Operação 0 = delete
            
    # Flag de controle do loop do protocolo de comunicação
    success = False 
    while not success:
        # Variavel que determina qual nó será comunicado
        primary_to_contact = primary_nodes[operation]
        try:
            # Tenta contato com o primário conhecido
            requests.post(f"http://{primary_to_contact}:8080/write_primary", json={"client_name": client_name, "value": new_client_string}, timeout=1)

            # Se a resposta dele foi bem sucedida, altera a flag de controle do loop
            print(f"[Rota write_request] | [{node_name}] | 🟢 Recebeu confirmação do servidor principal {primary_to_contact}\n", flush=True)
            success = True

        # Caso o primário tenha não responda, elege um novo primário
        except requests.exceptions.RequestException as e: 
            print(f"[Rota write_request: Exception] | [{node_name}] | ❌ Erro {e} na conexão com o primário {primary_nodes[operation]} da operação '{operation}'. Convocando eleição...", flush=True)
            
            # Envia o pedido de eleição para todos os outros nós que não são o primario. 
            # A lista é atualizada na eleicao, por isso, o primario antigo nunca é chamado
            for peer in peer_list:
                # Tenta falar com o nó
                try:
                    requests.get(f"http://{peer}:8080/elect_new_primary/{operation}", timeout=1)
                # Se não conseguir imprime erro
                except requests.exceptions.RequestException:
                    print(f"[Rota write_request: Exception Exception] | [{node_name}] | ❌ Erro {e} ao falar com o servidor {peer}", flush=True)
                    
            print(f"[Rota write_request] | ⚙️ Operação de eleição terminada. Lista de peers atual --> {peer_list}", flush=True)

    # Retorna sucesso ao servidor-cliente
    return jsonify({"status": "COMMITED"}), 200


# Rota ativada somente no servidor primário. Controla a escrita do banco dentro dele mesmo e faz o pedido de escrita aos demais servidores
@app.route("/write_primary", methods=["POST"])
def write_primary():
    global node_name, peer_list, primary_nodes
    
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

        # Caso não seja possível comunicar com o nó, convoca a eleição de um novo nó
        except requests.exceptions.RequestException as e: 
            print(f"[Rota write_primary: Exception] | {node_name} | ❌ Erro {e} na conexão com o servidor {peer}",flush=True)
            operation = primary_nodes.index(peer) # Obtendo de qual operaçào o peer morto é primario
            
            # Para cada peer dentro da lista que não é o peer morto (incluindo ele próprio), envia o pedido de eleição
            for other_peers in peer_list:
                # Não envia para o peer cuja conexão falhou
                if other_peers == peer:
                    continue
                # Tenta chamar a eleiçào para o peer
                try:
                    print(f"[Rota write_primary: Exception] | [{node_name}] | ⚠️ Notificando peer {other_peers}", flush=True)
                    requests.get(f"http://{other_peers}:8080/elect_new_primary/{operation}", timeout=1)
                # Caso não consiga, imprime erro
                except requests.exceptions.RequestException:
                    print(f"[Rota write_primary: Rerfesh Exception Exception] | {node_name} | ❌ Erro {e} na conexão com o servidor {other_peers}", flush=True)
    print(f"",flush=True)
    
    # Retorna código de sucesso
    return "", 200

# Rota que elege um novo nó primário. A cada chamada, é passada a operação que está sofrendo a troca de primários e o nó que assume é sempre o de maior número
@app.route("/elect_new_primary/<int:operation>", methods=["GET"])
def elect_new_primary(operation):
    global is_primary, peer_list, primary_nodes
    
    # Realizando o cast da operação, por garantia
    operation = int(operation)

    # Operação 0 = create, 1 = append, 2 = delete
    if operation == 0:
        print(f"\n[Rota elect_new_primary] | [{node_name}] | 👑 Eleição para create!", flush=True)
    elif operation == 1:
        print(f"\n[Rota elect_new_primary] | [{node_name}] | 👑 Eleição para append!", flush=True)
    else:    
        print(f"\n[Rota elect_new_primary] | [{node_name}] | 👑 Eleição para delete!", flush=True)

    # Obtenção do primário que será substituído (antigo)
    old_primary = primary_nodes[operation]
    print(f"[Rota elect_new_primary] | [{node_name}] | Nome do primário antigo --> {old_primary}", flush=True)

    # Remove o primário antigo da lista
    if old_primary in peer_list:
        peer_list.remove(old_primary)

    print(f"[Rota elect_new_primary] | [{node_name}] | Índice do novo primario --> {len(peer_list)-1}", flush=True)

    # O primário antigo é substituído pelo de maior número
    primary_nodes[operation] = peer_list[len(peer_list)-1]
    print(f"[Rota elect_new_primary] | [{node_name}] | Novo primario: {primary_nodes[operation]}", flush=True)

    # Se o primário for o próprio nó, altera a flag daquela operação
    if node_name == primary_nodes[operation]:
        print(f"[Rota elect_new_primary] | [{node_name}] | Sou o novo primário de {operation}.\n", flush=True)
        is_primary[operation] = True

    # Retorna sucesso
    return "", 200

# Rota que atualiza o banco de dados de um determinado cliente. A rota é ativada por um nó que não é o primário de uma operação
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
    
    # Retorna o código de sucesso
    return "", 200

# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200

# =================== ROTAS PARA A INTERFACE WEB ===================

# Rota que devolve as informações dos nós para o front-end. São passados quem sãos os primários de quais operações e as informações do banco de dados
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