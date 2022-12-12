import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH
import io
class Test_Nested_SSH():
    
    def test_Preparar_ambiente(self):
        
        assert True
    
    
    def test_maquina_ip_incorreto(self, mocker):
        gateway = {
            "ip": "servidor fake news",
            "port": 22,
            "login": "usuario",
            "pwd": "bazonga"
        }
        maquina = {
            "ip": "servidor fake news",
            "port": 22,
            "login": "usuario",
            "pwd": "bazonga"
        }
        # Bytes para que sofram decodificação dentro do método de extrair dados do comando
        erro = io.BytesIO("mensagem de erro\n".encode())
        saida =  io.BytesIO("machinename\n".encode())
        
        # Mock genérico para método de conectar do Paramiko
        mocker.patch("paramiko.SSHClient.connect", return_value=mocker.Mock())
        # Mock genérico para o método de obter transport
        mocker.patch("paramiko.SSHClient.get_transport", return_value=mocker.Mock())
        # define os valores de saída para o comando
        mocker.patch("paramiko.SSHClient.exec_command", return_value=(None, saida, erro))
        
        g = Nested_SSH(gateway_dados=gateway)
        assert g.executar(destino_dados=maquina, comando="hostname") == "machinename"
        

    
    
    