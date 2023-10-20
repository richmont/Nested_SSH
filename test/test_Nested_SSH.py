import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH
import io
import paramiko
import socket

counter_paramiko_connect=0
def definir_side_effect_mocker_paramiko_connect(*args, **kwargs):
    """Dependendo do contador, executa o método mocked de conexão do gateway ou do target_machine
    Requer que cada teste que use este método defina para zero a global counter_paramiko_connect
    """
    global counter_paramiko_connect
    if counter_paramiko_connect<=0:
        mocker_paramiko_connect_gateway(*args, **kwargs)
        counter_paramiko_connect+=1
    else:
        mocker_paramiko_connect_target_machine(*args, **kwargs)

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

def mocker_paramiko_connect_target_machine(*args, **kwargs):
        """
        Verifica se o login e endereço passado ao objeto connect são o esperado
        
        """
        
        hostname_inserido = args[0]
        
        senha_inserida = kwargs["password"]
        login_inserido = kwargs["username"]
        # se endereço timeout for inserido, sobe exceção socket.timeout
        if hostname_inserido == "endereco_timeout":
            raise socket.timeout
        # se valor do hostname for diferente de "endereco_certo", sobe erro de conexão
        
        if hostname_inserido != "endereco_certo_target_machine":
            raise socket.gaierror
        if senha_inserida != "senha_certa_target_machine" or login_inserido != "usuario_certo_target_machine":
            raise paramiko.AuthenticationException()
        try:
            sock_inserido = kwargs["sock"]
            if sock_inserido is not True:
                raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
        except KeyError:
            raise KeyError("não recebeu parametro sock, método connect sendo usado na ordem errada")

def mocker_paramiko_open_channel_target_machine(*args, **kwargs):
    
    tipo_conexao = args[0]
    try:
        arg_target_machine_endereco = args[1]
        arg_gateway_endereco = args[2]
        if arg_target_machine_endereco[0] == 'endereco_certo_target_machine' and arg_target_machine_endereco[1] == 22:
            assert True
        else:
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")

        if arg_gateway_endereco[0] == 'endereco_certo_gateway' and arg_gateway_endereco[1] == 22:
            assert True
        else:
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
    except IndexError:
        kwarg_target_machine_endereco = kwargs["dest_addr"]
        kwarg_gateway_endereco = kwargs["src_addr"]
        
        if tipo_conexao != 'direct-tcpip':
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
        
        
        
        if kwarg_target_machine_endereco[0] == 'endereco_certo_target_machine' and kwarg_target_machine_endereco[1] == 22:
            assert True
        else:
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")

        if kwarg_gateway_endereco[0] == 'endereco_certo_gateway' and kwarg_gateway_endereco[1] == 22:
            assert True
        else:
            raise paramiko.ssh_exception.ChannelException(404, "Conexão falhou, te vira ai")
    # método criaria um objeto a ser inserido no campo "sock" do método connect, então estou retornando True
    return True

def mocker_paramiko_exec_command_target_machine(*args):
    str_command_recebido = args[0]
    # Bytes para que sofram decodificação dentro do método de extrair dados do str_command
    erro = io.BytesIO("\n".encode())
    saida =  io.BytesIO("machinename\n".encode())
    entrada = io.BytesIO("hostname\n".encode())
    
    if str_command_recebido == "hostname":
        return entrada, saida, erro

def test_target_machine_tudo_certo(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_certo_target_machine",
        "port": 22,
        "login": "usuario_certo_target_machine",
        "pwd": "senha_certa_target_machine"
    }
    
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    # usa duas versões do connect mocked para gateway, depois para target_machine
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
        
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    
    g = Nested_SSH.Gateway(gateway_data=gateway)
    d = Nested_SSH.target_machine(g,machine_instance)
    resultado = d.executar("hostname")
    assert resultado == "machinename"
    d.encerrar()
    g.encerrar()

def test_Gateway_endereco_errado():
    """
    Provoca erro básico de falha de conexão
    """
    gateway = {
        "ip": "servidor fake news",
        "port": 22,
        "login": "usuario",
        "pwd": "bazonga"
    }
    machine_instance = {
        "ip": "servidor fake news",
        "port": 22,
        "login": "usuario",
        "pwd": "bazonga"
    }
    try:
        g = Nested_SSH(gateway_data=gateway)
        assert g.executar(machine_data=machine_instance, str_command="hostname")
    except Nested_SSH.errors.FailedConnection:
        assert True
    
def test_Gateway_porta_errada(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_certo",
        "port": 22222,
        "login": "login_gateway",
        "pwd": "senha_gateway"
    }
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    # usa duas versões do connect mocked para gateway, depois para target_machine
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
        
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        g.encerrar()
    except Nested_SSH.errors.EnderecoIncorreto:
        assert True

def test_target_machine_porta_errada(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_certo_target_machine",
        "port": 1212,
        "login": "usuario_certo_target_machine",
        "pwd": "senha_certa_target_machine"
    }
    
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    # usa duas versões do connect mocked para gateway, depois para target_machine
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
        
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        d = Nested_SSH.target_machine(g,machine_instance)
        resultado = d.executar("hostname")
        assert resultado == "machinename"
        d.encerrar()
        g.encerrar()
    except Nested_SSH.errors.FailedConnection:
        assert True


def test_target_machine_login_incorreto(mocker):

    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_errado",
        "pwd": "login_errado"
    }
    m_connect = mocker.MagicMock(side_effect=mocker_paramiko_connect_gateway)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        g.encerrar()
    except Nested_SSH.errors.AuthFailed:
        assert True

def test_target_machine_porta_errada(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_certo_target_machine",
        "port": 22,
        "login": "ablueuhae",
        "pwd": "aaaaaaaaaa"
    }
    
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    # usa duas versões do connect mocked para gateway, depois para target_machine
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
        
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        d = Nested_SSH.target_machine(g,machine_instance)
        resultado = d.executar("hostname")
        assert resultado == "machinename"
        d.encerrar()
        g.encerrar()
    except Nested_SSH.errors.AuthFailed:
        assert True
  
def test_target_machine_endereco_errado(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_certo_gateway",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_errado",
        "port": 22,
        "login": "root",
        "pwd": "senha_errada"
    }
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        d = Nested_SSH.target_machine(g,machine_instance)
        resultado = d.executar("hostname")
        assert resultado == "machinename"
        d.encerrar()
        g.encerrar()
    except Nested_SSH.errors.FailedConnection:
        assert True
        
def test_Gateway_timeout(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_timeout",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_errado",
        "port": 22,
        "login": "root",
        "pwd": "senha_errada"
    }
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        d = Nested_SSH.target_machine(g,machine_instance)
        resultado = d.executar("hostname")
        assert resultado == "machinename"
        d.encerrar()
        g.encerrar()
    except Nested_SSH.errors.EnderecoIncorreto:
        assert True
        
def test_target_machine_timeout(mocker):
    global counter_paramiko_connect
    counter_paramiko_connect=0
    gateway = {
        "ip": "endereco_correto",
        "port": 22,
        "login": "login_certo_gateway",
        "pwd": "senha_certa_gateway"
    }
    machine_instance = {
        "ip": "endereco_timeout",
        "port": 22,
        "login": "endereco_certo_target_machine",
        "pwd": "senha_certo_target_machine"
    }
    
    m_connect = mocker.MagicMock(side_effect=definir_side_effect_mocker_paramiko_connect)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    
    m_gateway_transport = mocker.MagicMock()
    m_gateway_transport.open_channel = mocker.MagicMock(side_effect=mocker_paramiko_open_channel_target_machine)
    m_exec_command_target_machine = mocker.MagicMock(side_effect=mocker_paramiko_exec_command_target_machine)    
    
    mocker.patch('paramiko.SSHClient.exec_command', m_exec_command_target_machine)
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", return_value=m_gateway_transport)
    try:
        g = Nested_SSH.Gateway(gateway_data=gateway)
        d = Nested_SSH.target_machine(g,machine_instance)
        resultado = d.executar("hostname")
        assert resultado == "machinename"
        d.encerrar()
        g.encerrar()
    except Nested_SSH.errors.EnderecoIncorreto:
        assert True