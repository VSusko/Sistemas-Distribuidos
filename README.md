Repositório para os trbalhos da disciplina de Sistemas Distribuídos

## Componentes

- **Flask** — aplicação principal
- **Redis** — armazenamento compartilhado (contador)
- **Kubernetes** — orquestração dos pods
  - `server-*` — instâncias que disputam a região crítica
  - `client-*` — clientes que disparam requisições para os servidores

---

## Como rodar

### 0. Tenha um Cluster Kind:
```bash
kind create cluster
```
### 1. Use o Makefile:
```bash
make all 
make apply
```
### 2. Verifique se tudo está no ar
```bash
kubectl get pods
```
### 3. Acesse um servidor e dispare uma eleição (simula entrada na região crítica)
```bash
kubectl exec -it server-0 -- bash
curl -X POST http://localhost:8080/elect -H "Content-Type: application/json" -d '{}'
```
### 4. Verifique o valor atual do contador no Redis:
```bash
kubectl exec -it redis-deployment-xxxxxxxxx-xxxxx -- redis-cli
GET shared_counter
```
### 5. Ver logs dos servidores:
```bash
kubectl logs -f server-0
kubectl logs -f server-1
...
```

## Outros comandos úteis
### 1. Variáveis de ambiente esperadas
Cada pod server-* precisa ter:

```bash
NODE_NAME=server-0
PEERS=server-0.server,server-1.server,server-2.server,server-3.server,server-4.server
REDIS_HOST=redis-service
```
### 2. Testar se a porta 8080 responde:
```bash
curl http://server-1.server:8080/request
```

