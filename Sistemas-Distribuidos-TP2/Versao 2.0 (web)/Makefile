IMAGE_CLIENT = victorsusko/client:web
IMAGE_INTERACTIVE_CLIENT = victorsusko/client-interactive:web
IMAGE_SERVER = victorsusko/server:web
IMAGE_CRITICAL = victorsusko/critical_server:web

# .PHONY garante que o make execute o comando mesmo que um arquivo com esse nome exista
.PHONY: all build-client push-client restart-client build-server push-server restart-server apply server client 

# --- Regras do Cliente ---
build-client:
	docker build -t $(IMAGE_CLIENT) ./client

push-client:
	docker push $(IMAGE_CLIENT)

build-i_client:
	docker build -t $(IMAGE_INTERACTIVE_CLIENT) ./interactive_client

push-i_client:
	docker push $(IMAGE_INTERACTIVE_CLIENT)

restart-client:
	kubectl rollout restart statefulset client

# --- Regras do Servidor ---
build-server:
	docker build -t $(IMAGE_SERVER) ./server

push-server:
	docker push $(IMAGE_SERVER)

restart-server:
	kubectl rollout restart statefulset server

# --- Regras do Servidor-extra ---
build-critical:
	docker build -t $(IMAGE_CRITICAL) ./critical_server

push-critical:
	docker push $(IMAGE_CRITICAL)

restart-critical:
	kubectl rollout restart statefulset server

delete:
	kubectl delete all --all

# --- Regras de conveniência ---

# Para criar os pods
apply:
	kubectl apply -f server-statefulset.yaml
	kubectl apply -f server-critical.yaml
	kubectl apply -f client-pods.yaml

# Para criar apenas os pods de server
server: 
	kubectl apply -f server-statefulset.yaml
	
# Para criar apenas o pod de critical server
critical: 
	kubectl apply -f server-critical.yaml

# Para criar apenas os pods de cliente
client: 
	kubectl apply -f client-pods.yaml

# Para deletar os pods
restart-cluster:	
	kind delete cluster
	kind create cluster --config kind-config.yaml

# Para fazer o build e push do cliente e server
build: build-client push-client build-i_client push-i_client build-server push-server build-critical push-critical

# Para fazer o build,push e criar todos os pods
b-app: build server critical client

# Para deletar todos os pods e posteriormente fazer build,push e criação
restart: restart-cluster b-app

# Para fazer build,push e resetar pods (as vezes nao funciona, melhor usar "make delete" seguido de "make b-app")
all: build-client push-client restart-client build-server push-server restart-server