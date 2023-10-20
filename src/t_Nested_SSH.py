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
        """Send the same comand to a list of machines

        Args:
            list_target_machines (list): List of machines addresses
            num_threads (int, optional): Number of threads to execute. Defaults to 3.
            
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
        self._queue_machines.join()  # wait queue end
        self.responses = self.extract_response()
        self.gateway.close()
        end_time = time.time()
        print("Time to execute:  ", end_time - start_time)

    def prepare_gateway(self, gateway_data):
        # replaced in a future version
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
            except Nested_SSH.Errors.FailedConnection:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error("Failed to connect to %s", machine_instance['ip'])
            except Nested_SSH.Errors.AuthFailed:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error("Authentication failure, check login and password %s", machine_instance['ip'])
            except Nested_SSH.Errors.WrongAddress:
                self._queue_responses.put(
                    {
                        "machine_instance": machine_instance["ip"],
                        "response": False,
                        "connection_sucessful": False
                    }
                    )
                logger.error("Wrong address: %s", machine_instance['ip'])
            self._queue_machines.task_done()

    def _fill_queue_machines(self):
        """Fill the queue with the addresses to be sended
        """
        for x in self._list_target_machines:
            self._queue_machines.put(x)

    def extract_response(self) -> list:
        """Gets from the response queue
        the list of dictionaries with the processing result

        Returns:
            list: list of dicts with the keys:
                - machine_instance (str): IP address of the machine
                - response (str): output of the command
                - connection_sucessful (bool): yes
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
