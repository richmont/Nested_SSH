import sys
import queue
from threading import Thread
import time
import logging
sys.path.append('..')
from .Nested_SSH import Nested_SSH
logger = logging.getLogger("Threads Nested_SSH")
logging.basicConfig(level=logging.INFO)


class t_Nested_SSH():
    def __init__(self, lista_maquinas, num_threads:int = 3, **kwargs) -> None:
        inicio = time.time()
        self.gateway_dados = kwargs["gateway"]
        self.comando = kwargs["comando"]
        self.lista_maquinas = lista_maquinas
        self.fila_maquinas = queue.Queue()
        self.fila_respostas = queue.Queue()

        self.gateway = self.preparar_gateway(self.gateway_dados)
        self.executar_threads(num_threads)
        self.preencher_filas_maquinas(self.fila_maquinas, self.lista_maquinas)
        self.fila_maquinas.join()  # aguarda fila terminar
        self.respostas = self.extrair_resultado(self.fila_respostas)
        self.gateway.encerrar()
        fim = time.time()
        print("Tempo para executar: ", fim - inicio)

    def preparar_gateway(self, gateway_dados):
        return Nested_SSH.Gateway(gateway_dados)

    def executar_comando(self):
        """Cria subprocesso que executa o ping pelo sistema operacional
        Usa como base a variável self.fila_ips
        Preenche self.fila_respostas com o resultado
        """
        while True:
            maquina = self.fila_maquinas.get()
            try:
                sessao_maquina = Nested_SSH.Destino(self.gateway, maquina)
                resposta = sessao_maquina.executar(self.comando)
                self.fila_respostas.put(
                    {
                        "maquina": maquina["ip"],
                        "resposta": resposta
                    }
                )
                sessao_maquina.encerrar()
            except Nested_SSH.erros.FalhaConexao:
                logger.error(f"Falha de conexão na máquina {maquina['ip']}")
            self.fila_maquinas.task_done()

    def preencher_filas_maquinas(self, fila_maquinas: queue.Queue, lista_maquinas: list):
        """Preenche a fila com valores dos enderecos a serem verificados

        Args:
            fila_maquinas (queue.Queue): Objeto fila que guarda os valores
            lista_maquinas (list): lista de enderecos recebida pelo objeto
        """
        for x in lista_maquinas:
            self.fila_maquinas.put(x)

    def extrair_resultado(self, fila_respostas: queue.Queue) -> list:
        """Obtém a partir da fila de respostas
        a lista dos dicionários com o resultado do processamento
        Args:
            fila_respostas (queue.Queue): Fila com informações obtidas dos pings

        Returns:
            list: lista de dicionários com IP(str) e resposta (bool)
        """
        lista_respostas = []
        while True:
            try:
                # obtém valor sem aguardar execução
                resposta = fila_respostas.get_nowait()
                lista_respostas.append(resposta)
            except queue.Empty:
                break  # quebra o laço quando lista fica vazia
        return lista_respostas

    def executar_threads(self, num_threads: int) -> None:
        """Executa o comando nested_ssh usando threads
        Args:
            num_threads (int): Número de threads a ser usada para processo
        """
        for x in range(1, num_threads):
            trabalhador = Thread(target=self.executar_comando)
            trabalhador.setDaemon(True)
            trabalhador.start()


if __name__ == "__main__":
    
    t = t_Nested_SSH(lista_maquinas, gateway=gateway, comando="")
    for x in t.respostas:
        print("Máquina: ", x["maquina"], " resposta do comando: ", x["resposta"])
