import threading   # Permite criar múltiplas threads para executar tarefas em paralelo
import time        # Usado para obter timestamps e pausar a execução (sleep)
import random      # Usado para gerar tempos aleatórios de espera entre requisições
import requests    # Usado para enviar requisições HTTP entre os containers

DEBUG = 1  # Flag de debug (pode ser usada para ativar prints mais detalhados)

# Número de clientes (threads) que serão executadas simultaneamente
CLIENTS_NUMBER = 5

# Função que define o comportamento de cada cliente (executada por cada thread)
def cliente_thread(cliente_id, sync_host):
    # Cada cliente faz 10 tentativas de acesso ao recurso R
    for i in range(10):
        timestamp = time.time()  # Obtém o tempo atual em segundos

        # Monta a mensagem que será enviada ao Cluster Sync
        message = {
            "client_id": cliente_id,     # ID do cliente
            "timestamp": timestamp,      # Tempo atual (para ordenação)
            "request": "WRITE"           # Tipo de requisição (escrita)
        }

        try:
            # Envia a requisição HTTP POST para o nó especificado do Cluster Sync
            response = requests.post(f'http://{sync_host}:5000/acesso', json=message)

            # Se a resposta for sucesso (200) e status COMMITTED, confirma a escrita
            if response.status_code == 200 and response.json().get("status") == "COMMITTED":
                print(f"[{cliente_id}] Escreveu no recurso R.")

        except Exception as e:
            # Caso ocorra algum erro na requisição (ex: nó fora do ar)
            print(f"[{cliente_id}] Erro ao enviar requisição: {e}")

        # Aguarda de 1 a 5 segundos aleatórios antes do próximo acesso
        time.sleep(random.randint(1, 5))

# Bloco principal: define e executa as threads dos clientes
if __name__ == "__main__":
    threads = []  # Lista para armazenar todas as threads

    for i in range(CLIENTS_NUMBER):
        cliente_id = f"client_{i+1}"           # Gera um ID legível para o cliente (ex: client_1, client_2, ...)
        sync_node = f"sync{i+1}"               # Nome do nó do Cluster Sync a ser contatado (ex: sync1, sync2, ...)

        # Cria a thread para o cliente
        t = threading.Thread(target=cliente_thread, args=(cliente_id, sync_node))
        threads.append(t)  # Adiciona a thread à lista
        t.start()           # Inicia a execução da thread

    # Aguarda todas as threads finalizarem antes de encerrar o programa
    for t in threads:
        t.join()
