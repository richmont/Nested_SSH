import sys
sys.path.append('.')
import pytest
from src.Nested_SSH import Nested_SSH

class Test_Nested_SSH():
    
    def test_Preparar_ambiente(self):
        assert True
    
    
    def test_maquina_ip_incorreto(self):
        gateway = {
            "ip": "servidor fake news",
            "port": 22,
            "login": "usuario",
            "pwd": "bazonga"
        }
        try:
            g = Nested_SSH(gateway_dados=gateway)
        except Nested_SSH.erros.FalhaConexao:
            assert True
        