import os       # Acesso a variáveis de ambiente
import time     # Para timestamps e pausas
import requests # Para enviar requisições HTTP
import random   

# Numero total de commits a serem requesitados pelo cliente
TOTAL_COMMITS = 50

# Obtém o nome do pod atual da variável de ambiente POD_NAME
# Exemplo: "client-2"
pod_name = os.getenv("POD_NAME", "client-0")  # Usa "client-0" se não encontrar

# Extrai o número final do nome do pod (ordinal)
# Ex: "client-2" → 2
ordinal = int(pod_name.split("-")[-1])

# Define o nome do servidor com base no ordinal
# Ex: server-2.server
target_server = f"server-{ordinal}.server"

print(f"🔵 [{pod_name}] falando com servidor: {target_server}")

commit_counter = 0
# Loop infinito: envia uma requisição a cada 5 segundos
while commit_counter < TOTAL_COMMITS:
    print(f'[{pod_name}]: tentativa de escrita número {commit_counter}', flush=True)
    try:
        # Gera um timestamp atual
        timestamp = time.time()
        print(f'[{pod_name}] timestamp: {timestamp}')

        # Envia uma requisição POST para /elect no servidor-alvo
        time.sleep(0.5)
        server_response = requests.post(f"http://{target_server}:8080/elect", json={"timestamp": timestamp, "client_name": pod_name})
        time.sleep(0.5)

        # Imprime a resposta do servidor
        print(f"🟢 [{pod_name}] resposta do servidor: {server_response.text}", flush=True)

    except Exception as e:
        # Em caso de erro, imprime a mensagem
        print(f"❌ [{pod_name}] erro: {e}", flush=True)

    # Espera entre 1 e 5 segundos antes da próxima tentativa
    if server_response.status_code == 200 and server_response.json().get("status") == "COMMITTED":
        print(f"[{pod_name}] Escreveu no recurso R.", flush=True)
        time.sleep(random.randint(1, 5))
    
    commit_counter+=1
