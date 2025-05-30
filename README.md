Para rodar tudo:
(primeiro tenha certeza de que está com o kubectl certo e funcionando)


kubectl apply -f mongo-deployment.yaml

kubectl apply -f app-ativo.yaml

(para verificar se está tudo rodando)
kubectl get all

(para deletar o pod e mostrar tolerancia a falha)
kubectl delete pod app-ativo

(verificar na base de dados se está recebendo tudo certo mesmo assim)
kubectl exec -it pod/mongo-689485f9f7-h9wxg -- bash

mongosh

use kube_db
db.messages.find().pretty()

(para scrollar)
it

PRONTO :)
