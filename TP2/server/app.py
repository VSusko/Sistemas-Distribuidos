from flask import Flask, request, jsonify
import threading
import time
import os
import requests

app = Flask(__name__)

node_name = os.getenv("NODE_NAME", "undefined")
peer_list = os.getenv("PEERS", "").split(",")  # Ex: "server-0,server-1,server-2"

# Estado local
request_timestamp = None
deferred_replies = []
using_critical = False
lock = threading.Lock()


@app.route("/request", methods=["POST"])
def on_request():
    global request_timestamp, using_critical

    data = request.json
    their_ts = data["timestamp"]
    their_node = data["node"]

    with lock:
        if using_critical or (request_timestamp and their_ts > request_timestamp):
            print(f"🔁 [{node_name}] deferiu para {their_node} (ts={their_ts:.4f})")
            return jsonify({"status": "WAIT"}), 202
        else:
            print(f"✅ [{node_name}] deu OK para {their_node} (ts={their_ts:.4f})")
            return jsonify({"status": "OK"}), 200


@app.route("/release", methods=["POST"])
def on_release():
    print(f"🔓 [{node_name}] liberou RC")
    return jsonify({"status": "RELEASED"}), 200


@app.route("/elect", methods=["POST"])
def elect():
    global request_timestamp, using_critical

    data = request.json
    client_ts = data.get("timestamp", time.time())

    # Inicia requisição com o timestamp recebido
    with lock:
        request_timestamp = client_ts
        using_critical = False

    print(f"\n📡 [{node_name}] recebeu pedido do cliente (ts={request_timestamp:.4f})")

    oks = 0
    for peer in peer_list:
        if peer == node_name:
            continue  # não envia para si mesmo
        try:
            url = f"http://{peer}:8080/request"
            res = requests.post(url, json={
                "timestamp": request_timestamp,
                "node": node_name
            }, timeout=1)
            if res.status_code == 200:
                oks += 1
        except Exception as e:
            print(f"⚠️ Falha ao contatar {peer}: {e}")

    if oks >= len(peer_list) - 1:
        with lock:
            using_critical = True
        print(f"🟢 [{node_name}] >>> Entrou na região crítica! ✅")
        time.sleep(3)

        # Libera RC
        for peer in peer_list:
            if peer == node_name:
                continue
            try:
                requests.post(f"http://{peer}:8080/release", timeout=1)
            except Exception as e:
                print(f"⚠️ Falha ao liberar RC para {peer}: {e}")
        with lock:
            using_critical = False
        print(f"🔴 [{node_name}] saiu da RC")
        return "Entered critical section", 200
    else:
        print(f"⛔ [{node_name}] não recebeu todos os OKs")
        return "Could not enter critical section", 409


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
