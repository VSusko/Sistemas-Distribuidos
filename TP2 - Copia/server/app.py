from flask import Flask, request, jsonify
import threading
import time
import os
import requests
import redis # NOVO

app = Flask(__name__)

node_name = os.getenv("NODE_NAME", "undefined")
peer_list = os.getenv("PEERS", "").split(",")

# --- NOVO: Conexão com o Redis ---
redis_host = os.getenv("REDIS_HOST", "localhost")
try:
    r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
    r.ping()
    print(f"✅ [{node_name}] Conectado ao Redis em {redis_host}")
except Exception as e:
    print(f"❌ [{node_name}] Falha ao conectar ao Redis: {e}")
    r = None
# ---------------------------------

# Estado local (sem alteração)
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
        # A lógica aqui foi simplificada para a prioridade por timestamp
        # Se eu estou usando a RC, ou se eu quero usar e meu timestamp é menor (maior prioridade)
        if using_critical or (request_timestamp is not None and request_timestamp < their_ts):
            print(f"🔁 [{node_name}] Deferiu para {their_node} (meu_ts={request_timestamp:.4f}, deles={their_ts:.4f})")
            return jsonify({"status": "WAIT"}), 202
        else:
            print(f"✅ [{node_name}] Deu OK para {their_node} (ts={their_ts:.4f})")
            return jsonify({"status": "OK"}), 200

# /release não precisa de alterações
@app.route("/release", methods=["POST"])
def on_release():
    print(f"🔓 [{node_name}] recebeu release")
    return jsonify({"status": "RELEASED"}), 200


@app.route("/elect", methods=["POST"])
def elect():
    global request_timestamp, using_critical

    data = request.json
    client_ts = data.get("timestamp", time.time())

    with lock:
        request_timestamp = client_ts
        using_critical = False

    print(f"\n📡 [{node_name}] recebeu pedido do cliente (ts={request_timestamp:.4f})")

    oks = 0
    # Como rodamos N servidores, precisamos de N-1 OKs.
    # Se só houver 1 servidor, ele entra direto.
    needed_oks = len(peer_list) - 1 if len(peer_list) > 1 else 0

    for peer in peer_list:
        try:
            if peer == node_name:
                url = "http://localhost:8080/request"
            else:
                url = f"http://{peer}:8080/request"
            
            print(f"📡 [{node_name}] tentando contactar {url}")
            
            res = requests.post(url, json={
                "timestamp": request_timestamp,
                "node": node_name
            }, timeout=2)

            if res.status_code == 200:
                oks += 1
                print(f'OKS --> {oks}')
        except Exception as e:
            print(f"⚠️ Falha ao contatar {peer}: {e}")

    if oks >= needed_oks:
        # --- ALTERADO: A REGIÃO CRÍTICA AGORA ACESSA O REDIS ---
        with lock:
            using_critical = True
        
        print(f"🟢 [{node_name}] >>> Entrou na região crítica! Acessando o Redis... ✅")
        
        # Simula a condição de corrida
        try:
            if not r:
                 raise ConnectionError("Sem conexão com o Redis")
            
            # 1. LER
            current_value_str = r.get('shared_counter')
            current_value = int(current_value_str) if current_value_str else 0
            
            print(f"    > [{node_name}] Valor lido do contador: {current_value}")
            
            # Pequeno delay para tornar a race condition mais óbvia se o lock falhar
            time.sleep(1) 
            
            # 2. MODIFICAR
            new_value = current_value + 1
            
            # 3. ESCREVER
            r.set('shared_counter', new_value)
            print(f"    > [{node_name}] Novo valor escrito: {new_value}")
            
        except Exception as e:
            print(f"❌ [{node_name}] Erro na região crítica: {e}")

        # -----------------------------------------------------------------

        # Libera RC
        print(f"🔴 [{node_name}] saindo da RC e liberando peers...")
        with lock:
            using_critical = False
            request_timestamp = None # Limpa o timestamp após o uso

        for peer in peer_list:
            if peer == node_name:
                continue
            try:
                requests.post(f"http://{peer}.server:8080/release", timeout=1)
            except Exception as e:
                print(f"⚠️ Falha ao liberar RC para {peer}: {e}")
        
        return "Entered critical section and updated Redis", 200
    else:
        print(f"⛔ [{node_name}] não recebeu {needed_oks} OKs (recebeu {oks})")
        return "Could not enter critical section", 409

if __name__ == "__main__":
    # Inicializa o contador no Redis se não existir
    if r:
        if not r.get('shared_counter'):
            r.set('shared_counter', 0)
    app.run(host="0.0.0.0", port=8080)