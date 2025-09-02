import os       # Acesso a variáveis de ambiente
import time     # Para timestamps e pausas
import requests # Para enviar requisições HTTP
import random   # Para fazer a espera randomica após o commit

# ==================== Variaveis do próprio cliente ====================
# Numero total de commits a serem requesitados pelo cliente
TOTAL_COMMITS = 500

# Obtém o nome do pod atual da variável de ambiente POD_NAME
# Exemplo: "client-2"
pod_name = os.getenv("POD_NAME", "client-0")  # Usa "client-0" se não encontrar

# Variavel do numero maximo de servidores
server_max_nodes = 5       

# ===================Espera pela inicialização dos servidores do cluster sync===================

for i in range(server_max_nodes):
    final_server = f"server-{i}.server"
    print(f"[Set-up step] | [{pod_name}] | Tentando conexão com servidor [{final_server}]")
    
    while True:
        try:
            response = requests.get(f"http://{final_server}:8080/isalive", timeout=1)
            print(f"[Set-up step] | [{pod_name}] | ✅ Conexão com [{final_server}] estabelecida!")
            break
        except Exception as e:
            print(f"[Set-up step] | [{pod_name}] | ⏳ {final_server} ainda não disponível...")

        time.sleep(1)  # Espera 1 segundo antes de tentar de novo

# ==================== Variaveis para comunicação com o cluster sync ====================
preferred_server_ordinal = int(pod_name.split("-")[-1])        # Extrai o número final do nome do pod (preferred_server_ordinal), ex: "client-2" → 2
preferred_server = f"server-{preferred_server_ordinal}.server" # Define o nome do servidor com base no preferred_server_ordinal, ex: server-2.server
commit_counter   = 0       # Variavel que conta os commits
server_nodes_selected = [] # Lista que armazena quais nós do cluster sync não responderam
command_list = ["create", "append", "delete"] # Lista de comandos os quais os clientes podem fazer

# Loop infinito: envia uma requisição randomicamente entre 1 e 5 segundos
while commit_counter < TOTAL_COMMITS:
    
    command_selection     = random.randint(0, 2) # Seleciona um comando aleatorio (create,update,delete)
    message               = f"{command_list[command_selection]} string{commit_counter}" # Gera uma string qualquer para enviar
    timestamp             = time.time()                 # Gera um timestamp atual
    server_node_selection = preferred_server_ordinal    # Escolhe o nó preferido  
    target_server         = preferred_server            # O primeiro servidor a ser tentado é o de numero correspondente ao cliente
    success               = False                       # Flag que controla o loop de requisições.
    
    print(f"\n[Request] | [{pod_name}] | 🟡 Tentativa de escrita número {commit_counter} | msg: '{message}'")
    
    # Enquanto não conseguir conectar a um server...
    while not success:
        # Tenta enviar uma requisição ao servidor
        try:
            print(f"[Request] | [{pod_name}] | 📨 Enviando pedido para o {target_server}")
            server_response = requests.post(f"http://{target_server}:8080/elect", json={"timestamp": timestamp, "client_name": pod_name, "value": message})

            # Se deu certo, altera a flag do loop e reseta a lista de servidores
            success = True
            server_nodes_selected.clear()
            print(f"[Request] | [{pod_name}] | ✅ [{pod_name}] resposta do servidor: {server_response.text}", flush=True)

        # Caso não seja possível comunicar com o pod, tenta conexão com o outro nó do cluster sync.
        except requests.exceptions.RequestException as e:
            print(f"[Request Exception] | [{pod_name}] | ❌ Erro {e} na conexão com o servidor {target_server}", flush=True)

            # Adicionando o servidor na lista de selecionados
            server_nodes_selected.append(server_node_selection) 

            # Se todos os servidores foram tentados e nenhum respondeu, reseta a lista e recomeça
            if len(server_nodes_selected) >= server_max_nodes:
                print(f"[Request Exception] | [{pod_name}] | ⏳ Nenhum servidor respondeu, aguardando...")
                time.sleep(3)
                server_nodes_selected.clear()
                target_server = preferred_server
            # Caso contrário, sorteia outro servidor
            else:
                while server_node_selection in server_nodes_selected:
                    server_node_selection = random.randint(0, server_max_nodes - 1)
                target_server = f"server-{server_node_selection}.server"

    # Dorme de 1 a 5 segundos antes de pedir novamente
    time.sleep(random.randint(1, 5))

    # Incrementando o contador de commit
    commit_counter += 1 