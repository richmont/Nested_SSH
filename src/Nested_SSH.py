import paramiko
import logging
import socket
logger = logging.getLogger("Nested_SSH")
logging.basicConfig(level=logging.INFO)
logging.getLogger('paramiko').setLevel("WARNING") # evita avisos de cada ação feita via SSH
"""
Código baseado na resposta
https://stackoverflow.com/questions/35304525/nested-ssh-using-python-paramiko
"""

class Nested_SSH():
    
    def __init__(self, gateway_dados: dict, timeout=1) -> None:
        """_summary_

        Args:
            timeout (int, optional): _description_. Defaults to 1.
        """
        self.gateway_dados = gateway_dados
        self.timeout = timeout
        
        
    def executar(self, destino_dados: dict, comando:str):
        """Executa um comando em servidor usando gateway como ponte

        Args:
            destino_dados (dict):
                ip (str): Endereço da máquina de destino
                port (str): Porta SSH
                login (str): Nome de usuário
                pwd (str): Senha
                
            comando (str): comando a ser executado no servidor de destino

        Raises:
            paramiko.ssh_exception.ChannelException: Falha de conexão

        Returns:
            resposta ao comando executado (str)
        """
        with paramiko.SSHClient() as gateway:
            gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                gateway.connect(self.gateway_dados["ip"], username=self.gateway_dados['login'], password=self.gateway_dados['pwd'], timeout=self.timeout)
            except socket.gaierror:
                raise Nested_SSH.erros.FalhaConexao("Conexão falhou no endereço do servidor: ", self.gateway_dados["ip"])
            gateway_transport = gateway.get_transport()
            local_addr = (self.gateway_dados["ip"], self.gateway_dados['port'])
            with paramiko.SSHClient() as destino:
                destino.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                dest_addr = (destino_dados["ip"], destino_dados["port"])
        
                
                try:
                    gateway_channel = gateway_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                    destino.connect(destino_dados["ip"], username=destino_dados["login"], password=destino_dados["pwd"], sock=gateway_channel, timeout=self.timeout)
                    stdin, stdout, stderr = destino.exec_command(comando)
                    erros = stderr.read().decode().strip("\n")
                    if len(erros) != 0:
                        logger.error(f"Erros na execução do comando {comando} no endereço {destino_dados['ip']}: {erros}")
                    return stdout.read().decode().strip("\n")
                except paramiko.ssh_exception.ChannelException:
                    #logger.error(f"Conexão falhou no endereço: {destino_dados['ip']}")
                    raise Nested_SSH.erros.FalhaConexao("Conexão falhou no endereço: ", destino_dados['ip'])

    class Gateway():
        def __init__(self, gateway_dados: dict, timeout:int=1) -> None:
            """Prepara um servidor intermediário como gateway para uso  
            
        Args:
            gateway_dados (dict): 
                ip: Endereço do servidor intermediário
                port: Porta SSH
                login: Nome de usuário
                pwd: Senha
            timeout (int, opcional): Limite do tempo de resposta para conexão. Padrão: 1.
        """
            self._gateway = paramiko.SSHClient()
            self._gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self._gateway.connect(gateway_dados["ip"], username=gateway_dados['login'], password=gateway_dados['pwd'], timeout=timeout)
                self.gateway_transport = self._gateway.get_transport()
                self.local_addr = (gateway_dados["ip"], gateway_dados['port'])
            except socket.gaierror:
                raise Nested_SSH.erros.EnderecoIncorreto("Verifique o endereço inserido: ", gateway_dados["ip"])

        def encerrar(self):
            """Encerra a conexão, importante!
            """
            self._gateway.close()

    class Destino():
        def __init__(self, gateway, destino_dados:dict, timeout:int=1) -> None:
            """Prepara um servidor de destino, após conexão com gateway, 
            para executar comando

            Args:
                gateway (Nested_SSH.Gateway): Gateway SSH preparado para receber conexões
                destino_dados (dict):
                    destino_dados (dict): 
                    ip: Endereço do servidor de execução
                    port: Porta SSH
                    login: Nome de usuário
                    pwd: Senha
                timeout (int, opcional): Limite do tempo de resposta para conexão. Padrão: 1.

            Raises:
                paramiko.ssh_exception.ChannelException: Falha de conexão
            """
            self._destino_dados = destino_dados
            self._destino = paramiko.SSHClient() 
            self._destino.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            dest_addr = (destino_dados["ip"], destino_dados["port"])
            try:
                gateway_channel = gateway.gateway_transport.open_channel("direct-tcpip", dest_addr, gateway.local_addr)
                self._destino.connect(destino_dados["ip"], username=destino_dados["login"], password=destino_dados["pwd"], sock=gateway_channel, timeout=timeout)
            except paramiko.ssh_exception.ChannelException:
                #logger.error(f"Conexão falhou no endereço: {destino_dados['ip']}")
                raise Nested_SSH.erros.FalhaConexao("Conexão falhou no endereço: ", destino_dados['ip'])

        def executar(self, comando:str) -> str:
            """Executa um comando no servidor de destino

            Args:
                comando (str): Comando bash

            Returns:
                str: Retorno do comando
            """
            stdin, stdout, stderr = self._destino.exec_command(comando)
            erros = stderr.read().decode().strip("\n")
            if len(erros) != 0:
                logger.error(f"Erros na execução do comando {comando} na máquina {self._destino_dados['ip']}: {erros}")
            return stdout.read().decode().strip("\n")
        
        def encerrar(self):
            """
            Encerra conexão, importante!
            """
            self._destino.close()
    
    class erros():
        class EnderecoIncorreto(Exception):
            pass
        class FalhaConexao(Exception):
            pass


