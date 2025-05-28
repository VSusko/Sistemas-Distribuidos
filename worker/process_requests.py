import os
import time
from google.cloud import firestore

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "chave-projeto.json"
db = firestore.Client()

print("Worker iniciado e escutando tarefas...")

while True:
    tarefas = db.collection("tarefas").where("status", "==", "pendente").stream()
    for tarefa in tarefas:
        data = tarefa.to_dict()
        print(f"Processando: {data['mensagem']}")
        db.collection("tarefas").document(tarefa.id).update({"status": "concluída"})
    time.sleep(2)
