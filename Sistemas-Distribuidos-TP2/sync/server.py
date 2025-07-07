from flask import Flask, request, jsonify
import socket, requests

TOTAL_NODES = 5
NODES = [f"sync{i+1}" for i in range(TOTAL_NODES)]
SELF = socket.gethostname()

app = Flask(__name__)

# ----- rota chamada pelo CLIENTE -----
@app.route('/client_request', methods=['POST'])
def client_request():
    msg = request.get_json() # Recebe a mensagem do cliente
    print(f'DEBUG| {msg}')
    timestamp  = msg["timestamp"]  # Captura o timestamp do cliente

    # monta payload de broadcast
    payload = {"sync_id": SELF, "timestamp": timestamp, "request": "WRITE"}

    ok_count = 1          # já conta ele mesmo
    for node in NODES:
        if node == SELF:                 # pula a si próprio
            continue
        try:
            response = requests.post(f"http://{node}:5000/cluster_sync", json=payload, timeout=2)
            if response.status_code == 200 and response.json().get("status") == "OK":
                ok_count += 1
        except Exception as e:
            print(f"[{SELF}] Falha ao falar c/ {node}: {e}")

    if ok_count == TOTAL_NODES:
        return jsonify({"status": "COMMITTED"}), 200
    else:
        return jsonify({"status": "ABORT"}), 500

# ----- rota chamada pelos OUTROS NÓS -----
@app.route('/cluster_sync', methods=['POST'])
def cluster_sync():
    msg = request.get_json()
    # aqui você poderia enfileirar/ordenar timestamps; por ora só devolvemos OK
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
