import os       # Acesso a variáveis de ambiente
import time     # Para timestamps e pausas
import requests # Para enviar requisições HTTP
import random   # Para fazer a espera randomica após o commit
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Nome do pod atual
pod_name = os.getenv("POD_NAME", "client-0")

# Número máximo de servidores no cluster
server_max_nodes = 5
server_nodes_selected = []

# Etapa de verificação: espera todos os servidores estarem prontos
for i in range(5):
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

# Nó preferido do cliente baseado no ordinal do pod
preferred_server_ordinal = int(pod_name.split("-")[-1])
preferred_server = f"server-{preferred_server_ordinal}.server"


# --- Rota principal do front-end ---
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form.get("message")  # Mensagem do cliente
        timestamp = time.time()
        success = False
        server_node_selection = preferred_server_ordinal
        target_server = preferred_server

        print(f"\n[{pod_name}] Tentando enviar mensagem: '{message}'")

        while not success:
            try:
                print(f"[{pod_name}] Enviando para {target_server}...")
                response = requests.post(
                    f"http://{target_server}:8080/elect",
                    json={
                        "timestamp": timestamp,
                        "client_name": pod_name,
                        "value": message
                    },
                    timeout=2
                )
                if response.status_code == 200:
                    print(f"[{pod_name}] ✅ Mensagem enviada com sucesso: {response.text}")
                    server_nodes_selected.clear()
                    success = True
                    return jsonify({
                        "status": "success",
                        "message": message,
                        "commit_message": "COMMITED"
                    }), 200
                else:
                    print(f"[{pod_name}] ❌ Erro no servidor {target_server}: {response.text}")
                    return jsonify({"status": "error", "message": response.text}), 500

            except requests.exceptions.RequestException as e:
                print(f"[{pod_name}] ❌ Erro ao conectar com {target_server}: {e}")
                server_nodes_selected.append(server_node_selection)

                if len(server_nodes_selected) >= server_max_nodes:
                    print(f"[{pod_name}] ⏳ Nenhum servidor respondeu, aguardando 3s...")
                    time.sleep(3)
                    server_nodes_selected.clear()
                    target_server = preferred_server
                else:
                    # Escolhe outro servidor aleatoriamente
                    while server_node_selection in server_nodes_selected:
                        server_node_selection = random.randint(0, server_max_nodes - 1)
                    target_server = f"server-{server_node_selection}.server"

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
