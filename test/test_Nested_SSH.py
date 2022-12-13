import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH
import io
import paramiko
class Test_Nested_SSH():

    
    @pytest.fixture()
    def mock_ssh_conexao_valida(self, mocker):
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
        return maquina, gateway
    
    @pytest.fixture()
    def verifica_senha(self, dict_login):
        pass
    
    
    def mock_connect(self, ip, username=None, password=None, timeout=1):
        if ip == "8.8.8.8":
            pass
        elif username == "usuario_valido":
            pass
        elif timeout == 2:
            pass
        else:
            raise(paramiko.ssh_exception.ChannelException())
    
    def test_maquina_exibindo_hostname_correto(self, mock_ssh_conexao_valida):
        maquina, gateway = mock_ssh_conexao_valida
        g = Nested_SSH(gateway_dados=gateway)
        assert g.executar(destino_dados=maquina, comando="hostname") == "machinename"
        
    def test_ip_incorreto(self):
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
        try:
            g = Nested_SSH(gateway_dados=gateway)
            assert g.executar(destino_dados=maquina, comando="hostname")
        except Nested_SSH.erros.FalhaConexao:
            assert True
    
    
    @pytest.fixture()
    def mock_ssh_login_invalido(self, mocker, mock_connect):

        gateway = {
            "ip": "8.8.8.8",
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
        mocker.patch("paramiko.SSHClient.connect", new=mock_connect)
        #paramiko.SSHClient.connect = mock_connect()
        # Mock genérico para o método de obter transport
        mocker.patch("paramiko.SSHClient.get_transport", return_value=mocker.Mock())
        # define os valores de saída para o comando
        mocker.patch("paramiko.SSHClient.exec_command", return_value=(None, saida, erro))
        return maquina, gateway
    
    def test_porta_errada(self):
        gateway = {
            "ip": "",
            "port": 22,
            "login": "",
            "pwd": ""
        }
        maquina = {
            "ip": "",
            "port": 22,
            "login": "",
            "pwd": ""
        }
        try:
            g = Nested_SSH(gateway_dados=gateway)
            g.executar(destino_dados=maquina, comando="hostname")
        except Nested_SSH.erros.FalhaAutenticacao:
            assert True
        
        
        