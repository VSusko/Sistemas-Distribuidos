# TP2 SD

# O que foi feito:

* Realizei um teste para ver se estou conseguindo fazer os containers comunicarem através do docker compose. 

* Para isso, criei duas pastas, uma para clientes e outra para o cluster sync. O docker criará um container que roda o aplicativo client.py, que basicamente cria 5 threads que servem como os clientes. Cada thread vai tentar entrar em contato com um, e apenas um, dos nós cluster sync. 

* Cada nó do cluster sync então vai responder com uma mensagem de que deu certo. Quem faz a mágica toda é o arquivo docker-compose, passei um tempo lendo a documentação dele hoje. Esse arquivo permite definir quantos containers vão ser criados, em que rede eles estão, o que acontece quando a aplicação termina, de onde vem a imagem do container, etc.

# O que ainda precisa ser feito:
Esse foi apenas um teste para ver se a comunicação entre containers está funcionando, e aparentemente está sim. Agora, podemos tentar dar os primeiros passos na parte difícil do tp, que é implementar o algoritmo de comunicação dos nós do cluster sync para resolver a questão da concorrência.
