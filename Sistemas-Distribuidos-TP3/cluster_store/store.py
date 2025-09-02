from flask import Flask, request, render_template # Framework web e utilitários para requisições/respostas
import os                        # Para acessar variáveis de ambiente (ex: nome do nó)
import requests

# Inicializa a aplicação Flask
app = Flask(__name__)  

# Nome do nó atual (definido via variável de ambiente, ex: NODE_NAME=db-1)
node_name = os.getenv("NODE_NAME", "undefined") + ".db"


# Definição do nó primario
if node_name == "db-2.db":
    is_primary_create = True
else:
    is_primary_create = False

if node_name == "db-1.db":
    is_primary_update = True
else:
    is_primary_update = False

if node_name == "db-0.db":
    is_primary_delete = True
else:
    is_primary_delete = False
    
# Nome do servidor primario do cluster store
primary_node_create = "db-2.db"
primary_node_update = "db-1.db"
primary_node_delete = "db-0.db"

# Lista de peers (outros nós do cluster store), recebida via variável de ambiente PEERS
# Exemplo: PEERS=db-0,db-1,db-2
peer_list = os.getenv("PEERS", "").split(",")

# Inicializando lista para armazenar as informações dos clientes
clients_database = [None] * 5

# =================== ROTAS PARA O PROTOCOLO DE COMUNICACAO ===================

# Rota que devolve a requisição de estabelecimento da conexão com os clientes
@app.route("/isalive", methods=["GET"])
def isalive():
    return "", 200

# Rota que atende as requisições de escrita do cliente
@app.route("/write_request", methods=["POST"])
def write_request():
    global node_name, peer_list, primary_node_create, primary_node_update, primary_node_delete
    
    # Obtendo dados do cliente
    data        = request.json        # Extração da mensagem
    client_name = data.get("node")    # Obtendo nome do servidor-cliente
    message   = data.get("value")   # Obtendo mensagem nova
    client_number = int(client_name.split("-")[-1]) # Obtendo a posição do cliente no banco
    instruction = message[7:]
    true_message = clients_database[client_number]
    
    print(f"[Rota write_request] | [{node_name}] | 🟡 Recebeu pedido do cliente [{client_name}] | Atual estado do banco: '{clients_database[client_number]}'. Chamando primário...", flush=True)
    
    # R1
    # Se quem recebeu o pedido foi o próprio primario, manda a rota para ele mesmo
    if message.startswith("create"):
        print("CREATE")
        true_message = instruction
        
        if is_primary_create == True:
            print(f"[Rota write_request] | [{node_name}] | 🗝️ Sou o próprio primário. Chamando rota write_primary...", flush=True)
            requests.post(f"http://{node_name}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
            
        # Se não for o primario, realiza o pedido de escrita para o nó primário
        else:
            # Variável que controla quando sair do loop. Ela se faz necessaria quando o primário morre e a chamada do primario precisa ser feita novamente
            success = False
            while not success:
                # Tenta contactar o primário
                try:
                    requests.post(f"http://{primary_node_create}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
                    print(f"[Rota write_request] | [{node_name}] |🟢 Recebeu confirmação do servidor principal'\n", flush=True)
                    success = True

                # Caso o primário tenha não responda, elege um novo
                except requests.exceptions.RequestException as e: 
                    print(f"[Rota write_request: Exception] | [{node_name}] | ❌ Erro {e} na conexão com o primário {primary_node_create}. Convocando eleição...", flush=True)
                    
                    # Envia o pedido de eleição para todos os outros nós que não são o primario. A lista é atualizada na eleicao, por isso, o primario antigo nunca eh chamado
                    for peer in peer_list:
                        try:
                            requests.get(f"http://{peer}:8080/elect_new_primary_create", timeout=1)

                        except requests.exceptions.RequestException:
                            print(f"[Rota write_request: Exception Exception] | [{node_name}] | ❌ Erro {e} ao falar com o servidor {peer}", flush=True)
                            
                    print(f"[Rota write_request] | ⚙️ Operação de eleição terminada. Lista de peers atual --> {peer_list}", flush=True)
    
    # R2
    # Se quem recebeu o pedido foi o próprio primario, manda a rota para ele mesmo
    elif message.startswith("update"):
        print("UPDATE")
        
        true_message = clients_database[client_number] + instruction
        
        if is_primary_update == True:
            print(f"[Rota write_request] | [{node_name}] | 🗝️ Sou o próprio primário. Chamando rota write_primary...", flush=True)
            requests.post(f"http://{node_name}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
            
        # Se não for o primario, realiza o pedido de escrita para o nó primário
        else:
            # Variável que controla quando sair do loop. Ela se faz necessaria quando o primário morre e a chamada do primario precisa ser feita novamente
            success = False
            while not success:
                # Tenta contactar o primário
                try:
                    requests.post(f"http://{primary_node_update}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
                    print(f"[Rota write_request] | [{node_name}] |🟢 Recebeu confirmação do servidor principal'\n", flush=True)
                    success = True

                # Caso o primário tenha não responda, elege um novo
                except requests.exceptions.RequestException as e: 
                    print(f"[Rota write_request: Exception] | [{node_name}] | ❌ Erro {e} na conexão com o primário {primary_node_update}. Convocando eleição...", flush=True)
                    
                    # Envia o pedido de eleição para todos os outros nós que não são o primario. A lista é atualizada na eleicao, por isso, o primario antigo nunca eh chamado
                    for peer in peer_list:
                        try:
                            requests.get(f"http://{peer}:8080/elect_new_primary_upload", timeout=1)

                        except requests.exceptions.RequestException:
                            print(f"[Rota write_request: Exception Exception] | [{node_name}] | ❌ Erro {e} ao falar com o servidor {peer}", flush=True)
                            
                    print(f"[Rota write_request] | ⚙️ Operação de eleição terminada. Lista de peers atual --> {peer_list}", flush=True)
                
    # R3
    # Se quem recebeu o pedido foi o próprio primario, manda a rota para ele mesmo
    elif message.startswith("delete"):
        print("DELETE")
        
        if instruction != "" or clients_database[client_number].find(instruction) != -1:
            true_message = clients_database[client_number].replace(f"{instruction}", "")
        else:
            # true_message = clients_database[client_number][:-1]
            print(f"pra remover só a última letra {clients_database[client_number][-1]}",flush=True)
            true_message = clients_database[client_number] - clients_database[client_number][-1]
            
        
        if is_primary_delete == True:
            print(f"[Rota write_request] | [{node_name}] | 🗝️ Sou o próprio primário. Chamando rota write_primary...", flush=True)
            requests.post(f"http://{node_name}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
            
        # Se não for o primario, realiza o pedido de escrita para o nó primário
        else:
            # Variável que controla quando sair do loop. Ela se faz necessaria quando o primário morre e a chamada do primario precisa ser feita novamente
            success = False
            while not success:
                # Tenta contactar o primário
                try:
                    requests.post(f"http://{primary_node_delete}:8080/write_primary", json={"client_name": client_name, "value": true_message}, timeout=1)
                    print(f"[Rota write_request] | [{node_name}] |🟢 Recebeu confirmação do servidor principal'\n", flush=True)
                    success = True

                # Caso o primário tenha não responda, elege um novo
                except requests.exceptions.RequestException as e: 
                    print(f"[Rota write_request: Exception] | [{node_name}] | ❌ Erro {e} na conexão com o primário {primary_node_delete}. Convocando eleição...", flush=True)
                    
                    # Envia o pedido de eleição para todos os outros nós que não são o primario. A lista é atualizada na eleicao, por isso, o primario antigo nunca eh chamado
                    for peer in peer_list:
                        try:
                            requests.get(f"http://{peer}:8080/elect_new_primary_delete", timeout=1)

                        except requests.exceptions.RequestException:
                            print(f"[Rota write_request: Exception Exception] | [{node_name}] | ❌ Erro {e} ao falar com o servidor {peer}", flush=True)
                            
                    print(f"[Rota write_request] | ⚙️ Operação de eleição terminada. Lista de peers atual --> {peer_list}", flush=True)
    else:
        print("Não começa com nenhum dos 3 prefixos...", flush=True)
    
    
    return "", 200

# Rota disparada quando um primário morre. É recebida por quem não é primário e não está atendendo clientes
@app.route("/elect_new_primary_create", methods=["GET"])
def elect_new_primary_create():
    global is_primary, peer_list, primary_node_create
    
    print(f"\n[Rota elect_new_primary_create] | [{node_name}] | 👑 Chamada de eleição do novo primário!", flush=True)
    print(f"[Rota elect_new_primary_create] | [{node_name}] | Nome do removido --> {primary_node_create}", flush=True)

    # Remove o primário da lista
    peer_list.remove(primary_node_create)
    # Elege o novo primário como sendo aquele com maior número
    primary_node_create = f"db-{len(peer_list)-1}.db"
    
    # Se o primário for o próprio nó, ativa a flag do primário
    if primary_node_create == node_name:
        print(f"[Rota elect_new_primary_create] | [{node_name}] | Sou o novo primário.\n", flush=True)
        is_primary = True
    
    return "", 200

@app.route("/elect_new_primary_update", methods=["GET"])
def elect_new_primary_update():
    global is_primary, peer_list, primary_node_update
    
    print(f"\n[Rota elect_new_primary_update] | [{node_name}] | 👑 Chamada de eleição do novo primário!", flush=True)
    print(f"[Rota elect_new_primary_update] | [{node_name}] | Nome do removido --> {primary_node_update}", flush=True)

    # Remove o primário da lista
    peer_list.remove(primary_node_update)
    # Elege o novo primário como sendo aquele com maior número
    primary_node_update = f"db-{len(peer_list)-1}.db"
    
    # Se o primário for o próprio nó, ativa a flag do primário
    if primary_node_update == node_name:
        print(f"[Rota elect_new_primary_update] | [{node_name}] | Sou o novo primário.\n", flush=True)
        is_primary = True
    
    return "", 200

@app.route("/elect_new_primary_delete", methods=["GET"])
def elect_new_primary_delete():
    global is_primary, peer_list, primary_node_delete
    
    print(f"\n[Rota elect_new_primary_delete] | [{node_name}] | 👑 Chamada de eleição do novo primário!", flush=True)
    print(f"[Rota elect_new_primary_delete] | [{node_name}] | Nome do removido --> {primary_node_delete}", flush=True)

    # Remove o primário da lista
    peer_list.remove(primary_node_delete)
    # Elege o novo primário como sendo aquele com maior número
    primary_node_delete = f"db-{len(peer_list)-1}.db"
    
    # Se o primário for o próprio nó, ativa a flag do primário
    if primary_node_delete == node_name:
        print(f"[Rota elect_new_primary_delete] | [{node_name}] | Sou o novo primário.\n", flush=True)
        is_primary = True
    
    return "", 200

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
                    print(f"[Rota write_primary: Rerfesh Exception] | [{node_name}] | ⚠️ Notificando peer {other_peers} da inanição de {peer}", flush=True)
                    requests.post(f"http://{other_peers}:8080/update_peers", json={"dead_peer": peer}, timeout=1)

                except requests.exceptions.RequestException:
                    print(f"[Rota write_primary: Rerfesh Exception Exception] | {node_name} | ❌ Erro {e} na conexão com o servidor {other_peers}", flush=True)
        
    print(f"",flush=True)
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

# # Rota para carregar a página web ao iniciar
# @app.route("/")
# def index():
#     return render_template("index.html",clients_database=clients_database,
#                            node_name=node_name,primary_node=primary_node,
#                            is_primary=is_primary)

@app.route("/")
def index():
    return render_template(
        "index.html",
        clients_database=clients_database,
        node_name=node_name,
        primary_node_create=primary_node_create,
        primary_node_update=primary_node_update,
        primary_node_delete=primary_node_delete,
        is_primary_create=is_primary_create,
        is_primary_update=is_primary_update,
        is_primary_delete=is_primary_delete
    )



# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)