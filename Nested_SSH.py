import paramiko
import logging
logger = logging.getLogger("Nested_SSH")
logging.basicConfig(level=logging.INFO)
logging.getLogger('paramiko').setLevel("WARNING") # evita avisos de cada ação feita via SSH
"""
Código baseado na resposta
https://stackoverflow.com/questions/35304525/nested-ssh-using-python-paramiko
"""

class Nested_SSH():
    def __init__(self, timeout=1, **kwargs) -> None:
        """Classe para comandos SSH utilizando um servidor como intermediário

        Args:
            gateway (dict): 
                ip: Endereço do servidor intermediário
                port: Porta SSH
                login: Nome de usuário
                pwd: Senha
                            
            destino (dict): 
                ip: Endereço da máquina de destino
                port: Porta SSH
                login: Nome de usuário
                pwd: Senha
                
            timeout (int, opcional): Limite do tempo de resposta para conexão. Padrão: 1.
        """
        self.gateway_dados = kwargs["gateway"]
        self.destino_dados = kwargs["destino"]
        self.timeout = timeout
        
        
    def executar(self, comando):
        with paramiko.SSHClient() as gateway:
            gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            gateway.connect(self.gateway_dados["ip"], username=self.gateway_dados['login'], password=self.gateway_dados['pwd'], timeout=self.timeout)
            gateway_transport = gateway.get_transport()
            local_addr = (self.gateway_dados["ip"], self.gateway_dados['port'])
            with paramiko.SSHClient() as pdv:
                pdv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                dest_addr = (self.destino_dados["ip"], self.destino_dados["port"])
    
                try:
                    gateway_channel = gateway_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                    pdv.connect(self.destino_dados["ip"], username=self.destino_dados["login"], password=self.destino_dados["pwd"], sock=gateway_channel, timeout=self.timeout)
                    stdin, stdout, stderr = pdv.exec_command(comando)
                    return stdout.read().decode().strip("\n")
                except paramiko.ssh_exception.ChannelException:
                    #logger.error(f"Conexão falhou no endereço: {self.destino_dados['ip']}")
                    raise paramiko.ssh_exception.ChannelException("Conexão falhou no endereço: ", self.destino_dados['ip'])



