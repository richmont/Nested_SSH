import paramiko
import logging
import socket
import struct
logger = logging.getLogger("Nested_SSH")
logging.basicConfig(level=logging.INFO)
logging.getLogger('paramiko').setLevel("WARNING") # evita avisos de cada ação feita via SSH
"""
Código baseado na resposta
https://stackoverflow.com/questions/35304525/nested-ssh-using-python-paramiko
"""

class Nested_SSH():
    
    def __init__(self, gateway_data: dict, timeout=1) -> None:
        """_summary_

        Args:
            timeout (int, optional): _description_. Defaults to 1.
        """

        self.gateway_data = gateway_data
        #if self.gateway_data["ip"] or self.gateway_data["port"] or self.gateway_data["login"] or self.gateway_data["pwd"] is None:
        #    raise TypeError("Valores do gateway inválidos, verifique e tente novamente")

        self.timeout = timeout

    def executar(self, machine_data: dict, str_command:str):
        """Executa um str_command em servidor usando gateway como ponte

        Args:
            machine_data (dict):
                ip (str): Endereço da máquina de target_machine
                port (str): Porta SSH
                login (str): Nome de usuário
                pwd (str): Senha
                
            str_command (str): str_command a ser executado no servidor de target_machine

        Raises:
            Nested_SSH.errors.FailedConnection: Falha de conexão

        Returns:
            resposta ao str_command executado (str)
        """
        with paramiko.SSHClient() as gateway:
            gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                gateway.connect(self.gateway_data["ip"], username=self.gateway_data['login'], password=self.gateway_data['pwd'], timeout=self.timeout)
            except socket.gaierror:
                raise Nested_SSH.errors.FailedConnection("Conexão falhou no endereço do servidor: ", self.gateway_data["ip"])
            except socket.timeout:
                    raise Nested_SSH.errors.FailedConnection("Conexão falhou no endereço, tempo de response expirou: ", self.gateway_data['ip'])
            gateway_transport = gateway.get_transport()
            local_addr = (str(self.gateway_data["ip"]), int(self.gateway_data['port']))
            with paramiko.SSHClient() as target_machine:
                target_machine.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                dest_addr = (str(machine_data["ip"]), int(machine_data["port"]))
        
                
                try:
                    gateway_channel = gateway_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                    target_machine.connect(machine_data["ip"], username=machine_data["login"], password=machine_data["pwd"], sock=gateway_channel, timeout=self.timeout)
                    stdin, stdout, stderr = target_machine.exec_command(str_command)
                    errors = stderr.read().decode().strip("\n")
                    if len(errors) != 0:
                        logger.error(f"errors na execução do str_command {str_command} no endereço {machine_data['ip']}: {errors}")
                    return stdout.read().decode().strip("\n")
                except paramiko.ssh_exception.ChannelException:
                    raise Nested_SSH.errors.FailedConnection("Conexão falhou no endereço: ", machine_data['ip'], " e porta ", machine_data['port'])
                except paramiko.ssh_exception.AuthenticationException:
                    raise Nested_SSH.errors.AuthFailed("Conexão falhou por autenticação, verifique usuário ou senha")
                
    class Gateway():
        def __init__(self, gateway_data: dict, timeout:int=1) -> None:
            """Prepara um servidor intermediário como gateway para uso  
            
        Args:
            gateway_data (dict): 
                ip: Endereço do servidor intermediário
                port: Porta SSH
                login: Nome de usuário
                pwd: Senha
            timeout (int, opcional): Limite do tempo de response para conexão. Padrão: 1.
        """
            self._gateway = paramiko.SSHClient()
            self._gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self._gateway.connect(gateway_data["ip"], username=gateway_data['login'], password=gateway_data['pwd'], timeout=timeout)
                self.gateway_transport = self._gateway.get_transport()
                self.local_addr = (str(gateway_data["ip"]), int(gateway_data['port']))
            except socket.gaierror:
                raise Nested_SSH.errors.EnderecoIncorreto("Verifique o endereço inserido: ", gateway_data["ip"])
            except socket.timeout:
                raise Nested_SSH.errors.EnderecoIncorreto("Verifique o endereço inserido: ", gateway_data["ip"], " tempo de espera expirou")
            except paramiko.ssh_exception.AuthenticationException:
                raise Nested_SSH.errors.AuthFailed("Verifique login e senha")

        def encerrar(self):
            """Encerra a conexão, importante!
            """
            self._gateway.close()

    class target_machine():
        def __init__(self, gateway, machine_data:dict, timeout:int=5) -> None:
            """Prepara um servidor de target_machine, após conexão com gateway, 
            para executar str_command

            Args:
                gateway (Nested_SSH.Gateway): Gateway SSH preparado para receber conexões
                machine_data (dict):
                    machine_data (dict): 
                    ip: Endereço do servidor de execução
                    port: Porta SSH
                    login: Nome de usuário
                    pwd: Senha
                timeout (int, opcional): Limite do tempo de response para conexão. Padrão: 1.

            Raises:
                paramiko.ssh_exception.ChannelException: Falha de conexão
            """
            self._machine_data = machine_data
            self._target_machine = paramiko.SSHClient() 
            self._target_machine.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            dest_addr = (str(machine_data["ip"]), int(machine_data["port"]))
            try:

                gateway_channel = gateway.gateway_transport.open_channel("direct-tcpip", dest_addr=dest_addr, src_addr=gateway.local_addr)
                self._target_machine.connect(machine_data["ip"], username=machine_data["login"], password=machine_data["pwd"], sock=gateway_channel, timeout=timeout, banner_timeout=200)
                logger.error(f"Conexão bem sucedida: {machine_data['ip']}")
            except paramiko.ssh_exception.ChannelException:
                logger.error(f"ChannelException: Conexão falhou no endereço: {machine_data['ip']}")
                raise Nested_SSH.errors.FailedConnection("Conexão falhou no endereço: ", machine_data['ip'])
            except struct.error:
                logger.error(f"struct.error: Conexão falhou no endereço: {machine_data['ip']}")
                raise Nested_SSH.errors.FailedConnection("Conexão falhou no endereço: ", machine_data['ip'])
            except paramiko.ssh_exception.AuthenticationException:
                logger.error(f"AuthenticationException: Verifique login e senha: {machine_data['ip']}")
                raise Nested_SSH.errors.AuthFailed("Verifique login e senha")
        def executar(self, str_command:str) -> str:
            """Executa um str_command no servidor de target_machine

            Args:
                str_command (str): str_command bash

            Returns:
                str: Retorno do str_command
            """
            stdin, stdout, stderr = self._target_machine.exec_command(str_command)
            errors = stderr.read().decode().strip("\n")
            if len(errors) != 0:
                logger.error(f"errors na execução do str_command {str_command} na máquina {self._machine_data['ip']}: {errors}")
            return stdout.read().decode().strip("\n")
        
        def encerrar(self):
            """
            Encerra conexão, importante!
            """
            self._target_machine.close()
    
    class errors():
        class EnderecoIncorreto(Exception):
            pass
        class FailedConnection(Exception):
            pass
        class AuthFailed(Exception):
            pass


