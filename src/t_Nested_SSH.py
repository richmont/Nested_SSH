from .Nested_SSH import Nested_SSH
import sys
import queue
from threading import Thread
import time
import logging
sys.path.append('..')

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
        start_time = time.time()
        self._gateway_data = kwargs["gateway"]
        self._str_command = kwargs["str_command"]
        self._list_target_machines = list_target_machines
        self._queue_machines = queue.Queue()
        self._queue_responses = queue.Queue()

        self.gateway = self.prepare_gateway(self._gateway_data)
        self.run_threads(num_threads)
        self._fill_queue_machines()
        self._queue_machines.join()  # aguarda fila terminar
        self.responses = self.extract_response()
        self.gateway.close()
        end_time = time.time()
        print("Time to execute:  ", end_time - start_time)

    def prepare_gateway(self, gateway_data):
        return Nested_SSH.Gateway(gateway_data)

    def execute_command(self):
        """Create subprocess to execute the command in the target machine
        
        Fill self._queue_responses
        """
        while True:
            machine_instance = self._queue_machines.get()
            try:
                session_machine = Nested_SSH.Target(self.gateway, machine_instance)
                response = session_machine.execute(self._str_command)
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": response,
                        "connection_sucessful": True
                    }
                )
                session_machine.close()
            except Nested_SSH.errors.FailedConnection:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Failed to connect to {machine_instance['ip']}")
            except Nested_SSH.errors.AuthFailed:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Authentication failure, check login and password {machine_instance['ip']}")
            except Nested_SSH.errors.WrongAddress:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error(f"Wrong address: {machine_instance['ip']}")
            self._queue_machines.task_done()

    def _fill_queue_machines(self):
        """Preenche a fila com valores dos enderecos a serem verificados

        Args:
            queue_machines (queue.Queue): Objeto fila que guarda os valores
            list_target_machines (list): lista de enderecos recebida pelo objeto
        """
        for x in self._list_target_machines:
            self._queue_machines.put(x)

    def extract_response(self) -> list:
        """Gets from the response queue
        the list of dictionaries with the processing result

        Returns:
            list: list of dicts with the keys:
            machine_instance (str): IP address of the machine
            "response": False,
            "connection_sucessful": False
        """
        list_responses = []
        while True:
            try:
                # get value without waiting execution
                response = self._queue_responses.get_nowait()
                list_responses.append(response)
            except queue.Empty:
                break  # break the loop when the queue is empty
        return list_responses

    def run_threads(self, num_threads: int) -> None:
        """Run the threads and execute the command
        Args:
            num_threads (int): Number of threads used for executing, keep the same for the number of machines.
        """
        for x in range(1, num_threads):
            proletariat = Thread(target=self.execute_command)
            proletariat.setDaemon(True)
            proletariat.start()


if __name__ == "__main__":

    pass
