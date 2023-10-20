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
    def __init__(self, list_target_machines, num_threads:int = 3, **kwargs) -> None:
        """Envia o mesmo str_command SSH para uma lista de máquinas

        Args:
            list_target_machines (list): Lista dos endereços das máquinas
            num_threads (int, optional): Número de threads a serem executadas. Defaults to 3.
            
        Kwargs:
            gateway_data (dict):
                ip (str):
                port (int):
                login (str):
                pwd (str):
        """
        inicio = time.time()
        self.gateway_data = kwargs["gateway"]
        self.str_command = kwargs["str_command"]
        self.list_target_machines = list_target_machines
        self.queue_machines = queue.Queue()
        self.queue_responses = queue.Queue()

        self.gateway = self.prepare_gateway(self.gateway_data)
        self.run_threads(num_threads)
        self.fill_queue_machines(self.queue_machines, self.list_target_machines)
        self.queue_machines.join()  # aguarda fila terminar
        self.responses = self.extract_response(self.queue_responses)
        self.gateway.encerrar()
        fim = time.time()
        print("Tempo para executar: ", fim - inicio)

    def prepare_gateway(self, gateway_data):
        return Nested_SSH.Gateway(gateway_data)

    def execute_command(self):
        """Cria subprocesso que executa o ping pelo sistema operacional
        Usa como base a variável self.fila_ips
        Preenche self.queue_responses com o resultado
        """
        while True:
            machine_instance = self.queue_machines.get()
            try:
                session_machine = Nested_SSH.target_machine(self.gateway, machine_instance)
                response = session_machine.executar(self.str_command)
                self.queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": response,
                        "connection_sucessful": True
                    }
                )
                session_machine.encerrar()
            except Nested_SSH.errors.FailedConnection:
                self.queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Falha de conexão na máquina {machine_instance['ip']}")
            except Nested_SSH.errors.AuthFailed:
                self.queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Falha de autenticação, verifique login e senha {machine_instance['ip']}")
            except Nested_SSH.errors.EnderecoIncorreto:
                self.queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Endereço incorreto: {machine_instance['ip']}")
            self.queue_machines.task_done()

    def fill_queue_machines(self, queue_machines: queue.Queue, list_target_machines: list):
        """Preenche a fila com valores dos enderecos a serem verificados

        Args:
            queue_machines (queue.Queue): Objeto fila que guarda os valores
            list_target_machines (list): lista de enderecos recebida pelo objeto
        """
        for x in list_target_machines:
            self.queue_machines.put(x)

    def extract_response(self, queue_responses: queue.Queue) -> list:
        """Obtém a partir da fila de responses
        a lista dos dicionários com o resultado do processamento
        Args:
            queue_responses (queue.Queue): Fila com informações obtidas dos pings

        Returns:
            list: lista de dicionários com IP(str) e response (bool)
        """
        list_responses = []
        while True:
            try:
                # obtém valor sem aguardar execução
                response = queue_responses.get_nowait()
                list_responses.append(response)
            except queue.Empty:
                break  # quebra o laço quando lista fica vazia
        return list_responses

    def run_threads(self, num_threads: int) -> None:
        """Executa o str_command nested_ssh usando threads
        Args:
            num_threads (int): Número de threads a ser usada para processo
        """
        for x in range(1, num_threads):
            proletariat = Thread(target=self.execute_command)
            proletariat.setDaemon(True)
            proletariat.start()


if __name__ == "__main__":

    pass
