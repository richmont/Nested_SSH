import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH
import io
import paramiko
import socket

contador_paramiko_connect=0
def definir_side_effect_mocker_paramiko_connect(*args, **kwargs):
    global contador_paramiko_connect
    if contador_paramiko_connect<=0:
        mocker_paramiko_connect_gateway(*args, **kwargs)
        contador_paramiko_connect+=1
    else:
        mocker_paramiko_connect_destino(*args, **kwargs)

def mocker_paramiko_connect_gateway(*args, **kwargs):
        """
        Verifica se o login e endereço passado ao objeto connect são o esperado
        
        """
        
        hostname_inserido = args[0]
        #assert hostname_inserido == 0
        senha_inserida = kwargs["password"]
        login_inserido = kwargs["username"]
        # se endereço timeout for inserido, sobe exceção socket.timeout
        if hostname_inserido == "endereco_timeout":
            raise socket.timeout
        # se valor do hostname for diferente de "endereco_certo", sobe erro de conexão
        if hostname_inserido != "endereco_certo_gateway":
            raise socket.gaierror
        if senha_inserida != "senha_certa_gateway" or login_inserido != "login_certo_gateway":
            raise paramiko.AuthenticationException()
        try:
            if kwargs["sock"]:
                raise TypeError("Objeto de conexão do gateway recebeu parâmetro de sock, está sendo usado no lugar errado")
        except KeyError:
            # método não recebeu parametro sock, então foi usado corretamente
            pass

def mocker_paramiko_connect_destino(*args, **kwargs):
        """
        Verifica se o login e endereço passado ao objeto connect são o esperado
        
        """
        
        hostname_inserido = args[0]
        sock_inserido = kwargs["sock"]
        senha_inserida = kwargs["password"]
        login_inserido = kwargs["username"]
        # se endereço timeout for inserido, sobe exceção socket.timeout
        if hostname_inserido == "endereco_timeout":
            raise socket.timeout
        # se valor do hostname for diferente de "endereco_certo", sobe erro de conexão
        
        if hostname_inserido != "endereco_certo_destino":
            raise socket.gaierror
        if senha_inserida != "senha_certa_destino" or login_inserido != "usuario_certo_destino":
            raise paramiko.AuthenticationException()
        if sock_inserido is not True:
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")

def mocker_paramiko_open_channel_destino(*args):
    
    tipo_conexao = args[0]
    destino_endereco = args[1]
    gateway_endereco = args[2]
    
    if tipo_conexao != 'direct-tcpip':
        raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
    
    if destino_endereco[0] == 'endereco_certo_destino' and destino_endereco[1] == 22:
        assert True
    else:
        raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")

    if gateway_endereco[0] == 'endereco_certo_gateway' and gateway_endereco[1] == 22:
        assert True
    else:
        raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
    # método criaria um objeto a ser inserido no campo "sock" do método connect, então estou retornando True
    return True


def mocker_paramiko_exec_command_destino(*args):
    comando_recebido = args[0]
    # Bytes para que sofram decodificação dentro do método de extrair dados do comando
    erro = io.BytesIO("\n".encode())
    saida =  io.BytesIO("machinename\n".encode())
    entrada = io.BytesIO("hostname\n".encode())
    
    if comando_recebido == "hostname":
        return entrada, saida, erro

    
def test_ip_incorreto():
    """
    Provoca erro básico de falha de conexão
    """
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
    

def test_Gateway_falha_conexao(mocker):
    gateway = {
        "ip": "endereco_certo",
        "port": 22222,
        "login": "login_gateway",
        "pwd": "senha_gateway"
    }
    
    
    try:
        g = Nested_SSH.Gateway(gateway_dados=gateway)
        g.encerrar()
    except Nested_SSH.erros.EnderecoIncorreto:
        assert True

def test_Gateway_login_incorreto(mocker):

    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_errado",
        "pwd": "login_errado"
    }
    m_connect = mocker.MagicMock(side_effect=mocker_paramiko_connect_gateway)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    try:
        g = Nested_SSH.Gateway(gateway_dados=gateway)
        g.encerrar()
    except Nested_SSH.erros.FalhaAutenticacao:
        assert True


def test_Destino_tudo_certo(mocker):
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    maquina = {
        "ip": "endereco_certo_destino",
        "port": 22,
        "login": "usuario_certo_destino",
        "pwd": "senha_certa_destino"
    }
    
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_destino)
    m_exec_command_destino = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_destino)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_destino)
    # usa duas versões do connect mocked para gateway, depois para destino
    
    m_connect_destino = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect_destino)
    
    #m_connect_gateway = mocker.MagicMock(side_effect=mocker_paramiko_connect_gateway)
    #mocker.patch("paramiko.SSHClient.connect", m_connect_gateway)
    
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    
    g = Nested_SSH.Gateway(gateway_dados=gateway)
    d = Nested_SSH.Destino(g,maquina)
    resultado = d.executar("hostname")
    assert resultado == "machinename"
    d.encerrar()
    g.encerrar()
    
    """
def test_Destino_endereco_errado(mocker):
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "richel277287",
        "pwd": "Batata;2"
    }
    maquina = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "root",
        "pwd": "xxxxxx"
    }
    
    # usa duas versões do connect mocked para gateway, depois para destino
    m_connect = mocker.MagicMock()
    m_connect.side_effect=[mocker_paramiko_connect_destino, mocker_paramiko_connect_gateway]
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_destino)
    m_exec_command_destino = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_destino)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_destino)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    
    g = Nested_SSH.Gateway(gateway_dados=gateway)
    d = Nested_SSH.Destino(g,maquina)
    resultado = d.executar("hostname")
    assert resultado == "machinename"
    d.encerrar()
    g.encerrar()
    """
    