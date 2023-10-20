# Nested_SSH
Biblioteca para enviar comandos SSH para máquinas através de um servidor SSH como gateway

## Classe Nested_SSH
Parâmetros:   
  
 __gateway_data__ (dict):  
- ip (str): endereco da máquina usada como gateway
- port (int): Porta usada para conexão SSH
- login (str): Login para acesso ao servidor
- pwd (str): Senha para acesso ao servidor

__timeout__ (int), opcional:   
- Tempo limite para considerar que a conexão foi malsucedida, valor padrão para 1

### Exemplo de uso
No script abaixo definimos os dados para a conexão da máquina com IP 192.168.1.12 através do gateway de IP 192.168.1.1. Preparamos os dados na forma de um dicionário e depois enviamos dois comandos:  
"hostname" e "echo 'hello world'", o resultado destes comandos são guardados em variáveis que são exibidas na tela com "print".  
```python
from src.Nested_SSH import Nested_SSH



maquina_destino = {
"ip": "192.168.1.12",
"port": 22,
"login": "joao",
"pwd": "senhamuitodificil"
}

dados_gateway = {
"ip": "192.168.1.1",
"port": 22,
"login": "maria",
"pwd":"senhadificil"
}
gateway = Nested_SSH(gateway_data=dados_gateway)
resultado_comando1 = gateway.execute(
    machine_data=maquina_destino,
    comando="hostname"
)
resultado_comando2 = gateway.execute(
machine_data=maquina_destino,
comando="echo 'hello world'"
)
print("Resultado do primeiro comando: ", resultado_comando1)
print("Resultado do segundo comando: ", resultado_comando2)
```

Ao executar este script teremos exibido na tela o seguinte:  

```
Resultado do primeiro comando: pc-joao  
Resultado do segundo comando: hello world  
```



## Classe t_Nested_SSH
Esta versão utiliza de threads para permitir que múltiplos comandos sejam enviados simultaneamente, agilizando o controle de múltiplas máquinas.  

### Parâmetros
__list_target_machines__ (list):  
Lista de dicionários com os dados das máquina de destino para o comando ser executado. Cada membro da lista deve conter as seguintes informações:  
- ip (str): endereco da máquina que receberá o comando
- port (int): Porta usada para conexão SSH
- login (str): Login para acesso a máquina
- pwd (str): Senha para acesso a máquina

 __gateway_data__ (dict):  
- ip (str): endereco da máquina usada como gateway
- port (int): Porta usada para conexão SSH
- login (str): Login para acesso ao servidor
- pwd (str): Senha para acesso ao servidor

__str_command__ (str):  
Comando que será executado em cada uma das máquinas.  

__num_threads__ (int), opcional, valor padrão = 3:  
Quantas threads serão usadas para a execução dos comandos. Recomendo que use 1 thread para cada máquina, um número maior não torna mais rápido.

### Resultado após o comando ser executado em todos os membros da lista de máquinas
__responses__ (list):  
Uma lista de dicionários com os valores a seguir:  
- __machine_instance__ (str): endereço IP da máquina onde o comando foi executado.  
- __response__ (str): Resposta ao comando executado, retorna o valor de stdout enquanto passa ao logger caso haja valores no stdout.  
- __connection_sucessful__ (bool): Conexão bem sucedida, True, malsucedida, False. Este valor trata apenas da conexão entre o gateway e a máquina, não se o comando foi executado corretamente.  
### Desempenho
Também é exibido em tela o tempo total para a execução de todos os comandos. Em uma listagem de 25 máquinas com 25 threads em uma LAN com 100mbps de banda levou 4,54s.  

### Exemplo de uso
```python
from src.t_Nested_SSH import t_Nested_SSH

lista_destinos = []
for _ in range(2,25):    
    maquina_destino = {
    "ip": f"192.168.0.{_}",
    "port": 22,
    "login": "usuario",
    "pwd": "senha"
    }
    lista_destinos.append(maquina_destino)

dados_gateway = {
"ip": "192.168.0.100",
"port": 22,
"login": "usuarioadm",
"pwd":"senhadificil"
}


gateway = t_Nested_SSH(
    list_target_machines=lista_destinos,
    gateway_data =dados_gateway,
    str_comand="hostname",
    num_threads=25
    )
for _ in gateway.respostas:
    print(_)
```
Partindo do princípio que temos 24 máquinas (IPs de 192.168.0.1 a 25) sendo acessadas pelo gateway de IP 192.168.0.100, executamos o comando "hostname" em todos os clientes. Para obter o resultado dos comandos, acessamos a variável "response" após a execução. Iteramos na lista de respostas e exibimos o dicionário com os valores.
```python
{'machine_instance': "192.168.0.13", 'response': 'estacao013', 'connection_sucessful': True}
{'machine_instance': "192.168.0.6" 'response': 'estacao006', 'connection_sucessful': True}
{'machine_instance': "192.168.0.10", 'response': 'estacao010', 'connection_sucessful': True}
{'machine_instance': "192.168.0.1" 'response': 'estacao001', 'connection_sucessful': True}
{'machine_instance': "192.168.0.17", 'response': 'estacao017', 'connection_sucessful': True}
{'machine_instance': "192.168.0.8" 'response': 'estacao008', 'connection_sucessful': True}
{'machine_instance': "192.168.0.18", 'response': 'estacao018', 'connection_sucessful': True}
{'machine_instance': "192.168.0.9" 'response': 'estacao009', 'connection_sucessful': True}
{'machine_instance': "192.168.0.14", 'response': 'estacao014', 'connection_sucessful': True}
{'machine_instance': "192.168.0.15", 'response': 'estacao015', 'connection_sucessful': True}
{'machine_instance': "192.168.0.21", 'response': 'estacao021', 'connection_sucessful': True}
{'machine_instance': "192.168.0.24", 'response': 'estacao024', 'connection_sucessful': True}
{'machine_instance': "192.168.0.23", 'response': 'estacao023', 'connection_sucessful': True}
{'machine_instance': "192.168.0.5" 'response': 'estacao005', 'connection_sucessful': True}
{'machine_instance': "192.168.0.19", 'response': 'estacao019', 'connection_sucessful': True}
{'machine_instance': "192.168.0.7" 'response': 'estacao007', 'connection_sucessful': True}
{'machine_instance': "192.168.0.12", 'response': 'estacao012', 'connection_sucessful': True}
{'machine_instance': "192.168.0.2" 'response': 'estacao002', 'connection_sucessful': True}
{'machine_instance': "192.168.0.4" 'response': 'estacao004', 'connection_sucessful': True}
{'machine_instance': "192.168.0.20", 'response': 'estacao020', 'connection_sucessful': True}
{'machine_instance': "192.168.0.22", 'response': 'estacao022', 'connection_sucessful': True}
{'machine_instance': "192.168.0.16", 'response': 'estacao016', 'connection_sucessful': True}
{'machine_instance': "192.168.0.3" 'response': 'estacao003', 'connection_sucessful': True}
{'machine_instance': "192.168.0.11", 'response': 'estacao011', 'connection_sucessful': True}
```
Nota-se que a ordem de entrada das máquinas, sequencial, foi diferente da ordem de saída, pois cada máquina respondeu em um momento diferente, devido ao paralelismo proporcionado pelas threads. A estação 13 retornou o resultado do comando mais rapidamente que a estação 11.

## Exceções
Mesmo a classe t_Nested_SSH aproveita as exceções lançadas por Nested_SSH.  

__Nested_SSH.Errors.WrongAddress__: Endereço IP informado, seja do gateway ou da máquina de destino, está incorreto.  
__Nested_SSH.Errors.AuthFailed__: Login ou senha informado está     incorreto.  
__Nested_SSH.Errors.FailedConnection__: Conexão para gateway ou a máquina de destino foi malsucedida.  