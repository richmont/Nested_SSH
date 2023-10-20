import paramiko
import logging
import socket
import struct
logger = logging.getLogger("Nested_SSH")
logging.basicConfig(level=logging.INFO)
logging.getLogger('paramiko').setLevel("WARNING") # evita avisos de cada ação feita via SSH
"""
Código baseado na resposta
https://stackoverflow.com/questions/35304525/nested-ssh-using-python-paramiko
"""

class Nested_SSH():
    
    def __init__(self, gateway_data: dict, timeout=1) -> None:
        """Allow execution 

        Args:
            timeout (int, optional): Defaults to 1.
        """

        self._gateway_data = gateway_data

        self._timeout = timeout

    def execute(self, machine_data: dict, str_command:str):
        """Execute a command without setup of a Gateway and Target manually

        Args:
            machine_data (dict):
                ip (str): Address of the target machine
                port (str): SSH port
                login (str): Username
                pwd (str): Password
                
            str_command (str): command to be executed in target machine

        Raises:
            Nested_SSH.Errors.FailedConnection: Connection failed

        Returns:
            response to command executed (str)
        """
        with paramiko.SSHClient() as gateway:
            gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                gateway.connect(
                    self._gateway_data["ip"],
                    username=self._gateway_data['login'],
                    password=self._gateway_data['pwd'],
                    timeout=self._timeout
                    )
            except socket.gaierror as e:
                raise Nested_SSH.Errors.FailedConnection(
                    "Connection failed at server: ", 
                    self._gateway_data["ip"]
                    ) from e
            except socket.timeout as e:
                raise Nested_SSH.Errors.FailedConnection(
                    "Conection failed at address, timeout: ", 
                    self._gateway_data['ip']
                    ) from e
            gateway_transport = gateway.get_transport()
            local_addr = (str(self._gateway_data["ip"]), int(self._gateway_data['port']))
            with paramiko.SSHClient() as target_machine:
                target_machine.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                dest_addr = (str(machine_data["ip"]), int(machine_data["port"]))

                try:
                    # create a channel connection to the gateway
                    gateway_channel = gateway_transport.open_channel(
                        "direct-tcpip", 
                        dest_addr, 
                        local_addr
                        )
                    # throught it, connect to the target
                    target_machine.connect(
                        machine_data["ip"], 
                        username=machine_data["login"],
                        password=machine_data["pwd"],
                        sock=gateway_channel,
                        timeout=self._timeout
                        )
                        # pipe stdin to temp variable, not used
                    _, stdout, stderr = target_machine.exec_command(str_command)
                    errors = stderr.read().decode().strip("\n")
                    if len(errors) != 0: # error occurred
                        logger.error("Errors in execution of %s at address %s: %s", str_command, machine_data['ip'], errors)
                    return stdout.read().decode().strip("\n") # get the output, clean it and return
                except paramiko.ssh_exception.ChannelException as e:
                    raise Nested_SSH.Errors.FailedConnection("connection failed at address: ", machine_data['ip'], " e porta ", machine_data['port'])
                except paramiko.ssh_exception.AuthenticationException as e:
                    raise Nested_SSH.Errors.AuthFailed("Connection failed because authentication, check login and password") from e

    class Gateway():
        """Class represents a gateway used to connect to a single or multiple targed machines"""
        def __init__(self, gateway_data: dict, timeout:int=1) -> None:
            """Prepare a gateway
            
        Args:
            gateway_data (dict): 
                ip: Address
                port: SSH port
                login: username
                pwd: password
            timeout (int, opt): time limit to connection, default 1
        """
            self._gateway = paramiko.SSHClient()
            self._gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self._gateway.connect(
                    gateway_data["ip"],
                    username=gateway_data['login'],
                    password=gateway_data['pwd'],
                    timeout=timeout
                    )
                self.gateway_transport = self._gateway.get_transport()
                # convert port value to int avoiding send str to socket
                self.local_addr = (
                    str(gateway_data["ip"]),
                    int(gateway_data['port'])
                    )
            except socket.gaierror as e:
                raise Nested_SSH.Errors.WrongAddress(
                    "Check the address inserted: ", 
                    gateway_data["ip"]
                    ) from e
            except socket.timeout as e:
                raise Nested_SSH.Errors.WrongAddress(
                    "Check the address inserted: ", 
                    gateway_data["ip"],
                    " timeout expired"
                    ) from e
            except paramiko.ssh_exception.AuthenticationException as e:
                raise Nested_SSH.Errors.AuthFailed("Check login and password") from e

        def close(self):
            """ close connection
            """
            self._gateway.close()

    class Target():
        """Class represents a target machine connected throught a gateway"""
        def __init__(self, gateway, machine_data:dict, timeout:int=5) -> None:
            """Prepare a target machine to execute commands

            Args:
                gateway (Nested_SSH.Gateway): Already prepared gateway
                machine_data (dict):
                    - ip: Address
                    - port: SSH port
                    - login: username
                    - pwd: password
                timeout (int, opt): time limit to connection, default 5

            Raises:
                paramiko.ssh_exception.ChannelException: Failed connection
            """
            self._machine_data = machine_data
            self._target_machine = paramiko.SSHClient() 
            self._target_machine.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            dest_addr = (str(machine_data["ip"]), int(machine_data["port"]))
            try:

                gateway_channel = gateway.gateway_transport.open_channel("direct-tcpip", dest_addr=dest_addr, src_addr=gateway.local_addr)
                self._target_machine.connect(machine_data["ip"], username=machine_data["login"], password=machine_data["pwd"], sock=gateway_channel, timeout=timeout, banner_timeout=200)
                logger.debug("Connection sucessful: %s", machine_data['ip'])
            except paramiko.ssh_exception.ChannelException as e:
                logger.error("ChannelException: Connection failed at address: %s", machine_data['ip'])
                raise Nested_SSH.Errors.FailedConnection("Connection failed at address: ", machine_data['ip']) from e
            except struct.error as e:
                logger.error("struct.error: Connection failed at address: %s", machine_data['ip'])
                raise Nested_SSH.Errors.FailedConnection("Connection failed at address: ", machine_data['ip']) from e
            except paramiko.ssh_exception.AuthenticationException as e:
                logger.error("AuthenticationException: Check login and password: %s", machine_data['ip'])
                raise Nested_SSH.Errors.AuthFailed("Check login and password") from e
        def execute(self, str_command:str) -> str:
            """Execute a command
            Args:
                str_command (str): string with the command

            Returns:
                str: default output of the command
            """
            _, stdout, stderr = self._target_machine.exec_command(str_command)
            errors = stderr.read().decode().strip("\n")
            if len(errors) != 0:
                logger.error("Error during the execution of command %s in machine %s: %s", str_command, self._machine_data['ip'], errors)
            return stdout.read().decode().strip("\n")

        def close(self):
            """
            Close the connection in the target machine
            """
            self._target_machine.close()

    class Errors():
        """Store all custom exceptions"""
        class WrongAddress(Exception):
            """Custom exception to wrong address"""
        class FailedConnection(Exception):
            """Custom exception to failed connection"""
        class AuthFailed(Exception):
            """Custom exception to authentication failed"""