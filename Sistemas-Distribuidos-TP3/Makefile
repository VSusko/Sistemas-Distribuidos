IMAGE_CLIENT = victorsusko/client:tp3
IMAGE_INTERACTIVE_CLIENT = victorsusko/client-interactive:tp3
IMAGE_SERVER = victorsusko/server:tp3
IMAGE_CLUSTER_STORE = victorsusko/cluster_store:tp3

# =================== Comandos para construcao do sistema =================== 

# .PHONY garante que o make execute o comando mesmo que um arquivo com esse nome exista
.PHONY: all build-client push-client restart-client build-server push-server restart-server apply server client db

# --- Regras do Cliente ---
build-client:
	docker build -t $(IMAGE_CLIENT) ./client

push-client:
	docker push $(IMAGE_CLIENT)

bp-client: build-client push-client

li-client: 
	kind load docker-image $(IMAGE_CLIENT)

# --- Regras do Cliente interativo ---
build-i_client:
	docker build -t $(IMAGE_INTERACTIVE_CLIENT) ./interactive_client

push-i_client:
	docker push $(IMAGE_INTERACTIVE_CLIENT)

bp-i-client: build-i_client push-i_client

li-i-client: 
	kind load docker-image $(IMAGE_INTERACTIVE_CLIENT)

# --- Regras do Servidor ---
build-server:
	docker build -t $(IMAGE_SERVER) ./cluster_sync

push-server:
	docker push $(IMAGE_SERVER)

bp-server: build-server push-server

li-server: 
	kind load docker-image $(IMAGE_SERVER)

# --- Regras do db backup---
build-db:
	docker build -t $(IMAGE_CLUSTER_STORE) ./cluster_store

push-db:
	docker push $(IMAGE_CLUSTER_STORE)

bp-db: build-db push-db

li-db: 
	kind load docker-image $(IMAGE_CLUSTER_STORE)

# ------ Regras de conveniência ------
delete:
	kubectl delete all --all

# Para criar apenas os pods do cluster sync
apply-server: 
	kubectl apply -f kubernetes/server-statefulset.yaml
	
# Para criar apenas os pods de cliente
apply-client: 
	kubectl apply -f kubernetes/client-pods.yaml

# Para criar apenas os pods do cluster store
apply-db: 
	kubectl apply -f kubernetes/db.yaml

# Para resetar os pods (utiliza o kubernetes local)
restart-cluster:	
	kind delete cluster
	kind create cluster --config kubernetes/kind-config.yaml

# Para fazer o build e push de todos os componentes
bp: bp-client bp-server bp-db bp-i-client

# Para criar os pods
apply: apply-server apply-client apply-db

# Para fazer todos os builds, pushes e criar todos os pods
b-apply: bp apply

# Para deletar todos os pods e posteriormente fazer build,push e criação
restart: restart-cluster b-apply

# Para fazer build,push e resetar pods (as vezes nao funciona, melhor usar "make delete" seguido de "make b-apply")
all: build-client push-client restart-client build-server push-server restart-server

# =================== Comandos do kubectl =================== 

# Mostrar todos os pods
getp:
	kubectl get pods

# Mostrar logs dos clientes
getc0:
	kubectl logs client-0
getc1:
	kubectl logs client-1
getc2:
	kubectl logs client-2
getc3:
	kubectl logs client-3
getc4:
	kubectl logs client-4

# Mostrar logs dos servidores do sync
gets0:
	kubectl logs server-0
gets1:
	kubectl logs server-1
gets2:
	kubectl logs server-2
gets3:
	kubectl logs server-3
gets4:
	kubectl logs server-4

# Mostrar logs dos servidores do store
getd0:
	kubectl logs db-0
getd1:
	kubectl logs db-1
getd2:
	kubectl logs db-2

# =================== Comandos de teste =================== 

# Comandos para desativar os pods do cluster store
deactivate-db-0:
	kubectl patch pod db-0 -p '{"spec":{"containers":[{"name":"db","image":"k8s.gcr.io/pause"}]}}'
deactivate-db-1:
	kubectl patch pod db-1 -p '{"spec":{"containers":[{"name":"db","image":"k8s.gcr.io/pause"}]}}'
deactivate-db-2:
	kubectl patch pod db-2 -p '{"spec":{"containers":[{"name":"db","image":"k8s.gcr.io/pause"}]}}'

# Teste 1: "deletar" um nó primario quando os 3 estão vivos. OBS: o kubernetes nao deixa deletar um nó que nao seja o ultimo. Por isso,
#  apenas faz com que o pod fique inativo
testdb0: deactivate-db-0

# Teste 2: Deletar o nó 1 do db
testdb1: deactivate-db-1

# Teste 3: Deletar o nó 2 do db
testdb2: deactivate-db-2

# Teste 2: Deletar os nós 0 e 1 do db
testdb3: deactivate-db-0 deactivate-db-1

# Teste 4: Deletar os nós 0 e 2 do db
testdb4: deactivate-db-0 deactivate-db-2

# Teste 5: Deletar os nós 1 e 2 do db
testdb5: deactivate-db-1 deactivate-db-2

# Comandos para desativar os pods do cluster sync
deactivate-sv-0:
	kubectl patch pod server-0 -p '{"spec":{"containers":[{"name":"server","image":"k8s.gcr.io/pause"}]}}'
deactivate-sv-1:
	kubectl patch pod server-1 -p '{"spec":{"containers":[{"name":"server","image":"k8s.gcr.io/pause"}]}}'
deactivate-sv-2:
	kubectl patch pod server-2 -p '{"spec":{"containers":[{"name":"server","image":"k8s.gcr.io/pause"}]}}'
deactivate-sv-3:
	kubectl patch pod server-3 -p '{"spec":{"containers":[{"name":"server","image":"k8s.gcr.io/pause"}]}}'
deactivate-sv-4:
	kubectl patch pod server-4 -p '{"spec":{"containers":[{"name":"server","image":"k8s.gcr.io/pause"}]}}'

# Teste 1: deletar apenas um nó
testsv1: deactivate-sv-0

# Teste 2: deletar 2 nós
testsv2: deactivate-sv-0 deactivate-sv-1

# Teste 3: deletar 3 nós
testsv3: deactivate-sv-0 deactivate-sv-1 deactivate-sv-2

# Teste 4: deletar os 4 primeiros nós
testsv4: deactivate-sv-0 deactivate-sv-1 deactivate-sv-2 deactivate-sv-3

# Teste 5: deletar os 4 ultimos nós
testsv5: deactivate-sv-1 deactivate-sv-2 deactivate-sv-3 deactivate-sv-4

# Teste 6: deletar os 4 aleatorios
testsv6: deactivate-sv-0 deactivate-sv-2 deactivate-sv-3 deactivate-sv-4