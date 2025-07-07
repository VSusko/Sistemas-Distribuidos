import os
import time
import requests

# server_host = os.getenv("SERVER_HOST", "server-service")
# port = 8080

# while True:
#     try:
#         url = f"http://{server_host}:{port}/elect"
#         response = requests.post(url)
#         print(f"Resposta do servidor: {response.status_code} - {response.text}")
#     except Exception as e:
#         print(f"Erro: {e}")
#     time.sleep(2)


pod_name = os.getenv("POD_NAME", "client-0")  # Ex: client-2
ordinal = int(pod_name.split("-")[-1])        # → 2
target_server = f"server-{ordinal}.server"    # → server-2.server

print(f"🔵 [{pod_name}] falando com servidor: {target_server}")

while True:
    try:
        timestamp = time.time()
        res = requests.post(
            f"http://{target_server}:8080/elect",
            json={"timestamp": timestamp}
        )
        print(f"🟢 [{pod_name}] resposta do servidor: {res.text}")
    except Exception as e:
        print(f"❌ [{pod_name}] erro: {e}")
    time.sleep(5)

