# Nested_SSH
Library for sending SSH commands to machines via an SSH server as a gateway

## Class Nested_SSH
Parameters:   
  
 __gateway_data__ (dict):  
- ip (str): address of the machine used as gateway
- port (int): SSH Port for connection
- login (str): Username for the server
- pwd (str): Password to the server

__timeout__ (int), opcional:   
- Time limit for server response, default value 1

### Exemplo de uso
In the script below we define the data for connecting the machine with IP 192.168.1.12 through the IP gateway 192.168.1.1. We prepare the data in the form of a dictionary and then send two commands:
"hostname" and "echo 'hello world'", the results of these commands are stored in variables that are displayed on the screen with "print".
```python
from src.Nested_SSH import Nested_SSH



target_machine = {
"ip": "192.168.1.12",
"port": 22,
"login": "joao",
"pwd": "veryhardpassword"
}

gateway_data = {
"ip": "192.168.1.1",
"port": 22,
"login": "maria",
"pwd":"hardpassword"
}
gateway = Nested_SSH(gateway_data=gateway_data)
command_result1 = gateway.execute(
    machine_data=target_machine,
    comando="hostname"
)
command_result2 = gateway.execute(
machine_data=target_machine,
comando="echo 'hello world'"
)
print("Result of the first command: ", command_result1)
print("Result of the second command ", command_result2)
```

When executing this script we will have the following displayed on the screen:
```
Result of the first command: pc-joao  
Result of the second command: hello world  
```



## Class t_Nested_SSH
This version uses threads to allow multiple commands to be sent simultaneously, streamlining the control of multiple machines.

### Parameters
__list_target_machines__ (list):  
List of dictionaries with data from the target machines for the command to be executed. Each list member must contain the following information: 
- ip (str): address of the machine that will receive the command
- port (int): Port used for SSH connection
- login (str): Login to access the server
- pwd (str): Password for server access

 __gateway_data__ (dict):  
- ip (str): address of the machine used as gateway
- port (int): Port used for SSH connection
- login (str): Login to access the server
- pwd (str): Password for server access

__str_command__ (str):  
Command that will be executed on each of the machines.

__num_threads__ (int), optional, default value = 3:  
How many threads will be used to execute the commands. I recommend using 1 thread for each machine, a higher number does not make it faster.

### Result after the command is executed on all members of the machine list
__responses__ (list):  
A list of dictionaries with the following values:
- __machine_instance__ (str): IP address of the machine where the command was executed. 
- __response__ (str): Response to the executed command, returns the value from stdout while passing it to the logger if there are values ​​in stdout.
- __connection_sucessful__ (bool): Connection successful, True, unsuccessful, False. This value only deals with the connection between the gateway and the machine, not whether the command was executed correctly.
### Performance
The total time for executing all commands is also displayed on the screen. On a list of 25 machines with 25 threads on a LAN with 100mbps of bandwidth it took 4.54s.

### Example of use
```python
from src.t_Nested_SSH import t_Nested_SSH

target_list = []
for _ in range(2,25):    
    target_machine = {
    "ip": f"192.168.0.{_}",
    "port": 22,
    "login": "user",
    "pwd": "password"
    }
    target_list.append(target_machine)

gateway_data = {
"ip": "192.168.0.100",
"port": 22,
"login": "rootuser",
"pwd":"hardpassword"
}


gateway = t_Nested_SSH(
    list_target_machines=target_list,
    gateway_data =gateway_data,
    str_comand="hostname",
    num_threads=25
    )
for _ in gateway.responses:
    print(_)
```
Assuming that we have 25 machines (IPs from 192.168.0.1 to 25) being accessed by the IP gateway 192.168.0.100, we execute the "hostname" command on all clients. To obtain the result of the commands, we access the "response" variable after execution. We iterate through the list of answers and display the dictionary with the values.
```python
{'machine_instance': "192.168.0.13", 'response': 'workstation013', 'connection_sucessful': True}
{'machine_instance': "192.168.0.6" 'response': 'workstation006', 'connection_sucessful': True}
{'machine_instance': "192.168.0.10", 'response': 'workstation010', 'connection_sucessful': True}
{'machine_instance': "192.168.0.1" 'response': 'workstation001', 'connection_sucessful': True}
{'machine_instance': "192.168.0.17", 'response': 'workstation017', 'connection_sucessful': True}
{'machine_instance': "192.168.0.8" 'response': 'workstation008', 'connection_sucessful': True}
{'machine_instance': "192.168.0.18", 'response': 'workstation018', 'connection_sucessful': True}
{'machine_instance': "192.168.0.9" 'response': 'workstation009', 'connection_sucessful': True}
{'machine_instance': "192.168.0.14", 'response': 'workstation014', 'connection_sucessful': True}
{'machine_instance': "192.168.0.15", 'response': 'workstation015', 'connection_sucessful': True}
{'machine_instance': "192.168.0.21", 'response': 'workstation021', 'connection_sucessful': True}
{'machine_instance': "192.168.0.24", 'response': 'workstation024', 'connection_sucessful': True}
{'machine_instance': "192.168.0.23", 'response': 'workstation023', 'connection_sucessful': True}
{'machine_instance': "192.168.0.5" 'response': 'workstation005', 'connection_sucessful': True}
{'machine_instance': "192.168.0.19", 'response': 'workstation019', 'connection_sucessful': True}
{'machine_instance': "192.168.0.7" 'response': 'workstation007', 'connection_sucessful': True}
{'machine_instance': "192.168.0.12", 'response': 'workstation012', 'connection_sucessful': True}
{'machine_instance': "192.168.0.2" 'response': 'workstation002', 'connection_sucessful': True}
{'machine_instance': "192.168.0.4" 'response': 'workstation004', 'connection_sucessful': True}
{'machine_instance': "192.168.0.20", 'response': 'workstation020', 'connection_sucessful': True}
{'machine_instance': "192.168.0.22", 'response': 'workstation022', 'connection_sucessful': True}
{'machine_instance': "192.168.0.16", 'response': 'workstation016', 'connection_sucessful': True}
{'machine_instance': "192.168.0.3" 'response': 'workstation003', 'connection_sucessful': True}
{'machine_instance': "192.168.0.11", 'response': 'workstation011', 'connection_sucessful': True}
```
It is noted that the machines' sequential input order was different from the output order, as each machine responded at a different time, due to the parallelism provided by the threads. Station 13 returned the command result faster than station 11.

## Exceptions
Even the t_Nested_SSH class takes advantage of exceptions thrown by Nested_SSH.

__Nested_SSH.Errors.WrongAddress__: The IP address entered, whether of the gateway or the destination machine, is incorrect. thrown by Nested_SSH.
__Nested_SSH.Errors.AuthFailed__: Login or password entered is incorrect.
__Nested_SSH.Errors.FailedConnection__: Connection to gateway or destination machine was unsuccessful.