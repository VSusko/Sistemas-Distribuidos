# Para rodar tudo:
(primeiro tenha certeza de que está com o kubectl certo e funcionando)


## 1. Aplique os manifests do MongoDB e do aplicativo
kubectl apply -f mongo-deployment.yaml

kubectl apply -f app-ativo.yaml

## 2. Verifique se todos os recursos estão rodando
kubectl get all


## 1. Delete o pod do app para simular uma falha
kubectl delete pod app-ativo

## 2. Verifique se o banco de dados continua recebendo os dados
kubectl exec -it pod/mongo-689485f9f7-h9wxg -- bash

## Dentro do container:
mongosh
use kube_db
db.messages.find().pretty()

## Para navegar entre os registros:
it


# PRONTO :)
