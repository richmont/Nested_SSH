# Nested_SSH
Biblioteca para enviar comandos SSH para máquinas através de um gateway como intermediário  

## Classe Nested_SSH
Parâmetros:   
  
 __gateway_dados__ (dict):  
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
import time


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
gateway = Nested_SSH(gateway_dados=dados_gateway)
resultado_comando1 = gateway.executar(
    destino_dados=maquina_destino,
    comando="hostname"
)
time.sleep(3)
resultado_comando2 = gateway.executar(
destino_dados=maquina_destino,
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

