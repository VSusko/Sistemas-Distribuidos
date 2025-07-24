IMAGE_CLIENT = victorsusko/client:latest
IMAGE_SERVER = victorsusko/server:latest

# .PHONY garante que o make execute o comando mesmo que um arquivo com esse nome exista
.PHONY: all build-client push-client restart-client build-server push-server restart-server apply server client 

# --- Regras do Cliente ---
build-client:
	docker build -t $(IMAGE_CLIENT) ./client

push-client:
	docker push $(IMAGE_CLIENT)

restart-client:
	kubectl rollout restart statefulset client

# --- Regras do Servidor ---
build-server:
	docker build -t $(IMAGE_SERVER) ./server

push-server:
	docker push $(IMAGE_SERVER)

restart-server:
	kubectl rollout restart statefulset server

# --- Regras de conveniência ---

# Para criar os pods
apply:
	kubectl apply -f server-statefulset.yaml
	kubectl apply -f client-statefulset.yaml

# Para criar apenas os pods de server
server: 
	kubectl apply -f server-statefulset.yaml

# Para criar apenas os pods de cliente
client: 
	kubectl apply -f client-statefulset.yaml

# Para deletar os pods
delete:	
	kubectl delete all --all

# Para fazer o build e push do cliente e server
build: build-client push-client build-server push-server

# Para fazer o build,push e criar todos os pods
b-app: build apply

# Para fazer build,push e resetar pods (as vezes nao funciona, melhor usar "make delete" seguido de "make b-app")
all: build-client push-client restart-client build-server push-server restart-server