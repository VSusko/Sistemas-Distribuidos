import os       # Para acessar variáveis de ambiente (ex: nome do nó)
import time     # Para marcar timestamps
import requests # Para enviar requisições HTTP para o servidor
from flask import Flask, render_template, request, jsonify  # Framework web e utilitários para requisições/respostas

# Inicializa a aplicação Flask
app = Flask(__name__)

# Obtém o nome do pod atual da variável de ambiente POD_NAME
pod_name = os.getenv("POD_NAME", "client-0")

# Etapa de verificação: espera todos os servidores estarem prontos
for i in range(5):
    final_server = f"server-{i}.server"
    print(f"[{pod_name}]: Tentando conexão com servidor [{final_server}]")
    
    while True:
        try:
            response = requests.get(f"http://{final_server}:8080/isalive")
            if response.status_code == 200:
                print(f"✅ [{pod_name}]: Conexão com [{final_server}] estabelecida!")
                break
        except Exception as e:
            print(f"⏳ [{pod_name}]: {final_server} ainda não disponível... {str(e)}")
            time.sleep(1)

# Extrai o número final do nome do pod (ordinal)
ordinal = int(pod_name.split("-")[-1])

# Define o nome do servidor com base no ordinal, no caso ambos serão sempre o server-0
target_server = f"server-{ordinal}.server"

#Rota para comunicação com o servidor e que lida com a interface web
@app.route("/", methods=["GET", "POST"])
def home():
    # Se a requisição é POST, realiza um pedido ao servidor 
    if request.method == "POST":
        # Obtenção do nome do cliente pela caixa de texto enviada no json
        client_name = request.form.get("client_name")
        # Obtenção do timestamp
        timestamp = time.time()
        print(f"[{pod_name}]: Enviando pedido para {target_server} com client_name={client_name}, timestamp={timestamp}")

        # Tentativa de escrita no recurso
        try:
            # Usa a rota elect para comunicar com o server-0
            response = requests.post(f"http://{target_server}:8080/elect",json={"timestamp": timestamp, "client_name": client_name})

            # Se o retorno do server foi bem-sucedido, retorna à interface web uma mensagem de COMMITED
            if response.status_code == 200:
                print(f"[{pod_name}]: Sucesso")
                # Mensagem json: sucesso, nome do cliente, timestamp e COMMITED
                return jsonify({
                    "status": "success",
                    "client_name": client_name,
                    "timestamp": timestamp,
                    "commit_message": "COMMITED"
                }), 200
            else:
            # Se o retorno do server foi mal-sucedido, reporta o erro
                print(f"[{pod_name}]: Erro no servidor {target_server}: {response.text}")
                return jsonify({
                    "status": "error",
                    "message": f"Erro no servidor: {response.text}"
                }), 500
        # Em caso de erro da comunicação com o servidor, reporta o erro
        except Exception as e:
            print(f"[{pod_name}]: Erro na comunicação com {target_server}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Erro na comunicação: {str(e)}"
            }), 500

    # Se a requisição é GET, apenas renderiza a página web
    return render_template("index.html")

# Inicia o servidor Flask escutando em todas as interfaces, na porta 8080
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)