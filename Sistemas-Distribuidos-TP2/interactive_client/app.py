import os
import time
import requests
from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__)

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define o nome do pod
pod_name = os.getenv("POD_NAME", "client-0")

# Verificação: espera todos os servidores estarem prontos
for i in range(5):
    final_server = f"server-{i}.server"
    logger.info(f"[{pod_name}]: Tentando conexão com servidor [{final_server}]")
    
    while True:
        try:
            response = requests.get(f"http://{final_server}:8080/isalive")
            if response.status_code == 200:
                logger.info(f"✅ [{pod_name}]: Conexão com [{final_server}] estabelecida!")
                break
        except Exception as e:
            logger.warning(f"⏳ [{pod_name}]: {final_server} ainda não disponível... {str(e)}")
            time.sleep(1)

ordinal = int(pod_name.split("-")[-1])
target_server = f"server-{ordinal}.server"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        client_name = request.form.get("client_name")
        timestamp = time.time()
        logger.info(f"[{pod_name}]: Enviando pedido para {target_server} com client_name={client_name}, timestamp={timestamp}")

        try:
            response = requests.post(f"http://{target_server}:8080/elect",json={"timestamp": timestamp, "client_name": client_name})
            if response.status_code == 200:
                # Assume que o servidor retorna um JSON com mensagem de commit
                logger.info(f"[{pod_name}]: Sucesso")
                return jsonify({
                    "status": "success",
                    "client_name": client_name,
                    "timestamp": timestamp,
                    "commit_message": "COMMITED"
                }), 200
            else:
                logger.error(f"[{pod_name}]: Erro no servidor {target_server}: {response.text}")
                return jsonify({
                    "status": "error",
                    "message": f"Erro no servidor: {response.text}"
                }), 500
        except Exception as e:
            logger.error(f"[{pod_name}]: Erro na comunicação com {target_server}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Erro na comunicação: {str(e)}"
            }), 500

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)