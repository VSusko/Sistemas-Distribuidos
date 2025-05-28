import os
from google.cloud import firestore
import time

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../chave-projeto.json"
db = firestore.Client()

for i in range(10):
    db.collection("tarefas").add({
        "mensagem": f"Requisição {i}",
        "status": "pendente"
    })
    print(f"Enviado: Requisição {i}")
    time.sleep(1)
