import os
from google.cloud import firestore

# Caminho para o arquivo JSON da chave de serviço
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "chave-projeto.json"

# Conecta ao Firestore
db = firestore.Client()

# Adiciona um documento
db.collection("mensagens").add({"texto": "Olá", "status": "pendente"})
