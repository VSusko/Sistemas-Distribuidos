IMAGE_CLIENT = cristianomafuz/client:latest
IMAGE_SERVER = cristianomafuz/server:latest

# .PHONY garante que o make execute o comando mesmo que um arquivo com esse nome exista
.PHONY: all build-client push-client restart-client build-server push-server restart-server apply

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
apply:
	kubectl apply -f server-statefulset.yaml
	kubectl apply -f client-statefulset.yaml
	
all: build-client push-client restart-client build-server push-server restart-server