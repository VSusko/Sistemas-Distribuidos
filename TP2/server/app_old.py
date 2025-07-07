from flask import Flask, request
import redis
import os
import time
import random

# # Ocultar logs HTTP
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


app = Flask(__name__)

# Conectando ao Redis Service do Kubernetes
redis_host = os.getenv("REDIS_HOST", "redis")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

node_name = os.getenv("NODE_NAME", "undefined")
lock_key = "election_lock"
lock_ttl = 3  # segundos

@app.route("/elect", methods=["POST"])
def elect():
    delay = random.randint(10, 100) / 1000.0
    time.sleep(delay)

    # Tenta adquirir o lock usando SETNX
    elected = r.set(lock_key, node_name, nx=True, ex=lock_ttl)

    if elected:
        print(f"\n🟢 [{node_name}] >>> VENCEU a eleição! (delay={delay:.3f}s)\n")
        return f"Node {node_name} elected", 200
    else:
        current_leader = r.get(lock_key)
        print(f"🔴 [{node_name}] perdeu. Líder atual: {current_leader}")
        return f"Already elected: {current_leader}", 409


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
