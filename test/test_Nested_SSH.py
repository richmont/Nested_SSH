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

    
def test_maquina_exibindo_hostname_correto(mock_ssh_conexao_valida):
    maquina, gateway = mock_ssh_conexao_valida
    g = Nested_SSH(gateway_dados=gateway)
    assert g.executar(destino_dados=maquina, comando="hostname") == "machinename"
    
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
    


def test_porta_errada(mocker):
    
    gateway = {
        "ip": "endereco_gateway",
        "port": 22222,
        "login": "login_gateway",
        "pwd": "senha_gateway"
    }
    maquina = {
        "ip": "endereco_maquina",
        "port": 22222,
        "login": "login_maquina",
        "pwd": "senha_maquina"
    }
    # Bytes para que sofram decodificação dentro do método de extrair dados do comando
    erro = io.BytesIO("mensagem de erro\n".encode())
    saida =  io.BytesIO("machinename\n".encode())
    
    
    def side_effect_sobe_excecao_porta_errada(*args):
        """
        Verifica se as portas passadas ao objeto são compatíveis com o esperado
        """
        tipo_conexao = args[0] # por padrão, direct-tcpip
        tupla_endereco_destino = args[1] # 0 = ip, 1 = porta
        tupla_endereco_local = args[2] # 0 = ip, 1 = porta
        porta_destino = tupla_endereco_destino[1]
        
        porta_local = tupla_endereco_local[1]
        if porta_destino != 22 or porta_local != 22:
            raise Nested_SSH.erros.FalhaConexao()
         
    
    m_connect = mocker.MagicMock()
    m_transport = mocker.MagicMock()
    m_open_channel = mocker.MagicMock(return_value=10, side_effect=side_effect_sobe_excecao_porta_errada) # recebe a porta para conexao com maquina
    m_transport.open_channel = m_open_channel
    m_get_transport = mocker.MagicMock(return_value=m_transport)
    m_exec_commmand = mocker.MagicMock(return_value=(None, saida, erro))

    mocker.patch("paramiko.SSHClient.connect", m_connect)
    mocker.patch("paramiko.SSHClient.get_transport", m_get_transport)
    mocker.patch("paramiko.SSHClient.exec_command", m_exec_commmand)
    try:
        g = Nested_SSH(gateway_dados=gateway)
        g.executar(destino_dados=maquina, comando="hostname")
    except Nested_SSH.erros.FalhaConexao:
        assert True

    """
    assert m_connect.call_args_list == [
            mocker.call('endereco_gateway', username='login_gateway', password='senha_gateway', timeout=1),
            mocker.call('endereco_maquina', username='login_maquina', password='senha_maquina', sock=10, timeout=1)
            ]
    """
    
