# importa MongoClient (para conexão) e erros específicos do PyMongo
from pymongo import MongoClient, errors
import time       # para controlar timestamp e delays
import os         # para ler variáveis de ambiente
import signal     # para capturar sinais de término (SIGTERM/SIGINT)
import sys        # para encerrar o processo com sys.exit

# obtém o host do Mongo a partir de variável de ambiente, ou usa "mongo-service" como padrão
mongo_host = os.getenv("MONGO_HOST", "mongo-service")

# cria uma conexão com o MongoDB, limitando o timeout de seleção de servidor a 3 segundos
client = MongoClient(
    f"mongodb://{mongo_host}:27017/",
    serverSelectionTimeoutMS=3000
)

# seleciona o banco e a coleção onde as mensagens serão gravadas
db = client["kube_db"]
collection = db["messages"]

# lê o nome do pod de uma variável de ambiente, para identificação nos logs
pod_name = os.getenv("POD_NAME", "pod-unknown")


def send_message(i=0):
    """
    Constrói um documento com:
      - from: nome do pod
      - msg: mensagem de texto "hello{i}"
      - ts: timestamp atual
    e tenta inserir na coleção.
    Em caso de erro de conexão ou inserção, captura PyMongoError e loga no stdout.
    """
    doc = {
        "from": pod_name,
        "msg": f"hello{i}",
        "ts": time.time()
    }
    try:
        collection.insert_one(doc)
        print(f"[{pod_name}] Mensagem enviada: {doc}")
    except errors.PyMongoError as e:
        print(f"[{pod_name}] Erro ao enviar mensagem: {e}")


def handle_exit(signum, frame):
    """
    Função de callback para sinais de término (SIGTERM/SIGINT).
    Fecha a conexão com o MongoDB e encerra o processo graciosamente.
    """
    print(f"[{pod_name}] Encerrando...")
    client.close()
    sys.exit(0)


# registra handle_exit para sinais de término e interrupção (Ctrl+C)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)


if __name__ == "__main__":
    # bloco principal: informa que o processo iniciou
    print(f"[{pod_name}] Iniciando envio de mensagens para o MongoDB...")
    i = 0
    # loop infinito: envia uma mensagem a cada 5 segundos
    while True:
        send_message(i)
        i += 1
        time.sleep(5)
