import os       # Acesso a variáveis de ambiente
import time     # Para timestamps e pausas
import requests # Para enviar requisições HTTP
import random   # Para fazer a espera randomica após o commit
from flask import Flask, render_template, request, jsonify # Framework web e utilitários para requisições/respostas

# ==================== Variaveis do próprio cliente ====================
# Inicia a aplicação web do flask
app = Flask(__name__)

# Obtém o nome do pod atual da variável de ambiente POD_NAME
# Exemplo: "client-2"
pod_name = os.getenv("POD_NAME", "client-0")

# Variavel do numero maximo de servidores
server_max_nodes = 5       

# ===================Espera pela inicialização dos servidores do cluster sync===================

for i in range(server_max_nodes):
    final_server = f"server-{i}.server"
    print(f"[Set-up step] | [{pod_name}] | Tentando conexão com servidor [{final_server}]", flush = True)
    
    while True:
        try:
            response = requests.get(f"http://{final_server}:8080/isalive", timeout=1)
            print(f"[Set-up step] | [{pod_name}] | ✅ Conexão com [{final_server}] estabelecida!", flush=True)
            break
        except Exception as e:
            print(f"[Set-up step] | [{pod_name}] | ⏳ {final_server} ainda não disponível...", flush=True)
        time.sleep(1)

# ==================== Variaveis para comunicação com o cluster sync ====================
server_nodes_selected    = []  # Lista que armazena quais nós do cluster sync não responderam
preferred_server_ordinal = int(pod_name.split("-")[-1])  # Extrai o número final do nome do pod (preferred_server_ordinal), ex: "client-2" → 2
preferred_server         = f"server-{preferred_server_ordinal}.server" # O primeiro servidor a ser tentado é o de numero correspondente ao cliente

# Rota usada para interação com o cliente via interface web e troca de mensagens com os servidores
@app.route("/", methods=["GET", "POST"])
def home():
    # Se o método for POST, ou seja, envio de mensagens para os servidores...
    if request.method == "POST":
        # Captura o input do usuario mensagem enviada pelo botão
        message = request.form.get("message", "").strip()

        # Validação mensagem vazia
        if not message:
            return jsonify({"status": "error", "message": "Mensagem vazia"}), 400

        # Obtem o timestamp, seleciona o servidor e o servidor-target
        timestamp             = time.time()
        server_node_selection = preferred_server_ordinal
        target_server         = preferred_server
        print(f"\n[Rota principal] | [{pod_name}] | Enviando mensagem: '{message}'", flush = True)

        success = False # Variavel de controle do loop de requisições.
        # Enquanto não conseguir conectar a um server...
        while not success:
            # Tenta enviar mensagem a um servidor do cluster sync, envia a mensagem e o timestamp
            try:
                print(f"[{pod_name}] Enviando para {target_server}...", flush=True)
                response = requests.post(f"http://{target_server}:8080/elect",json={"timestamp": timestamp,"client_name": pod_name,"value": message},timeout=2)

                # Se os servidores conseguem realizar a operação, retorna código 200
                if response.status_code == 200:
                    print(f"[Rota principal] | [{pod_name}] | ✅ Mensagem enviada com sucesso: {response.text}", flush=True)
                    # Limpa a lista de servidores não conectados
                    server_nodes_selected.clear()
                    # Ativa a variável de controle do loop
                    success = True
                    # Retorna mensagem de sucesso para o front-end
                    return jsonify({"status": "success", "message": message, "commit_message": "COMMITED"}), 200
                else:
                    # Em caso de erro na conexão, apenas imprime no log 
                    print(f"[Rota principal] | [{pod_name}] | ❌ Erro no servidor {target_server}: {response.text}", flush=True)

            # Caso não seja possível comunicar com o pod, tenta conexão com o outro nó do cluster sync.
            except requests.exceptions.RequestException as e:
                
                # Captura de exceção da conexão com o servidor. Adiciona o servidor que nào respondeu dentro da lista
                print(f"[{pod_name}] ❌ Erro ao conectar com {target_server}: {e}. Tentando proximo servidor...", flush = True)
                server_nodes_selected.append(server_node_selection)

                # Se todos os servidores foram tentados e nenhum respondeu, desiste da aplicação
                if len(server_nodes_selected) >= server_max_nodes:
                    print(f"[{pod_name}] ❌ Nenhum servidor respondeu", flush=True)
                    return jsonify({"status": "error", "message": response.text}), 500
                # Caso contrário, seleciona outro servidor para enviar a mensagem
                else:
                    # Seleciona aleatoriamente algum servidor que ainda não foi tentado
                    while server_node_selection in server_nodes_selected:
                        server_node_selection = random.randint(0, server_max_nodes - 1)
                    target_server = f"server-{server_node_selection}.server"
    
    # Retorna a pagina web
    return render_template("index.html")

# Aplicação do flex rodando na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
