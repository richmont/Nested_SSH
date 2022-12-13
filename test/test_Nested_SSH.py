import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH
import io
import paramiko 


@pytest.fixture()
def mock_ssh_conexao_valida(mocker):
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
def verifica_senha(dict_login):
    pass


    
def test_maquina_exibindo_hostname_correto(mock_ssh_conexao_valida):
    maquina, gateway = mock_ssh_conexao_valida
    g = Nested_SSH(gateway_dados=gateway)
    assert g.executar(destino_dados=maquina, comando="hostname") == "machinename"
    
def test_ip_incorreto():
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
    

def mock_ssh_login_invalido(mocker, mock_connect_maquina, mock_connect_gateway):

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
    mocker.patch("paramiko.SSHClient.connect", new=mock_connect_gateway)
    #paramiko.SSHClient.connect = mock_connect()
    # Mock genérico para o método de obter transport
    mocker.patch("paramiko.SSHClient.get_transport", return_value=mocker.Mock())
    # define os valores de saída para o comando
    mocker.patch("paramiko.SSHClient.exec_command", return_value=(None, saida, erro))
    return maquina, gateway

def test_porta_errada(mocker):
    gateway = {
        "ip": "endereco_gateway",
        "port": 22,
        "login": "login_gateway",
        "pwd": "senha_gateway"
    }
    maquina = {
        "ip": "endereco_maquina",
        "port": 22,
        "login": "login_maquina",
        "pwd": "senha_maquina"
    }
    # Bytes para que sofram decodificação dentro do método de extrair dados do comando
    erro = io.BytesIO("mensagem de erro\n".encode())
    saida =  io.BytesIO("machinename\n".encode())
    
    m_connect = mocker.MagicMock()
    m_transport = mocker.MagicMock()
    m_open_channel = mocker.MagicMock(return_value=10)
    m_transport.open_channel = m_open_channel
    m_get_transport = mocker.MagicMock(return_value=m_transport)
    m_exec_commmand = mocker.MagicMock(return_value=(None, saida, erro))
    
    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", m_get_transport)
    mocker.patch("paramiko.SSHClient.exec_command", m_exec_commmand)
    g = Nested_SSH(gateway_dados=gateway)
    g.executar(destino_dados=maquina, comando="hostname")
    assert m_connect.call_args_list == [
            
            mocker.call('endereco_gateway', username='login_gateway', password='senha_gateway', timeout=1),
            mocker.call('endereco_maquina', username='login_maquina', password='senha_maquina', sock=10, timeout=1)
            ]
    
    
