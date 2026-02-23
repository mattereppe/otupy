from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.os import OS
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.network_function import NetworkFunction
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.server import Server
from otupy.profiles.xbom.data.network_node import NetworkNode
from otupy.profiles.xbom.data.execution_environment import ExecutionEnvironment
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.data.api import API
from otupy.profiles.xbom.data.web_service import WebService
from otupy.types.base import Choice
from otupy.core.extensions import Register

class ServiceType(Choice):
    
    register = Register({'application': Application, 'execution_environment': ExecutionEnvironment, 'vm': VM, 
            'server': Server, 'os': OS, 'pod': Pod, 'container': Container, 'host': Host, 'network_node': NetworkNode,
        'api': API, 'cloud': Cloud, 'network': Network, 'network_function': NetworkFunction, 'iot': IOT})

    def __init__(self, service_type):
        super().__init__(service_type)
