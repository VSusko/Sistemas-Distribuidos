# TP2 SD

# Como executar o TP:

* Primeiramente, substitua nos arquivos .yaml e no makefile as imagens do docker para a sua imagem no docker hub (estará algo como victorsusko/client:latest)

# Comandos makefile

* Depois, basta fazer "make build". Se voce alterou os arquivos e quer ver as modificações, o seu docker vai ser atualizado com o novo arquivo alterado. Caso contrário, vai pegar a versão que tem salva aí.

* Agora use o comando "make apply" que o kubernetes vai criar todos os pods.

* Alternativamente, o comando make b-app faz os dois últimos na sequência

# Ver containers e logs

* O comando "kubectl get pods" permite ver quantos e quais pods foram criados. Uma vez que o pod estiver com o status "RUNNING", é possivel visualizar o log dele com o comando "kubectl logs [nomedopod]". Os pods aqui estão dispostos de client-0 a client-4 e de server-0 a server-4.
* Vale dizer que o comando "kubectl logs [nomedopod]" vai mostrar o log até o momento em que voce digitou esse comando. Alternativamente, é possível acompanhar em tempo real o log do pod com a diretiva '-f', então o comando fica "kubectl -f logs [nomedopod]". Para sair desse modo, aperte CTRL+C

# OBS

* Pode acontecer de quando voce mudar os arquivos, as alterações não aparecerem visivelmente. Se isso acontecer, delete o cluster com "make delete" e depois faça a parte 'Comandos makefile' de novo
