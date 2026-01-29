from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.iot import IOT
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.vm import VM
from otupy.profiles.ctxd.data.computer import Computer
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.network_service import NetworkService
from otupy.types.base import Choice
from otupy.core.extensions import Register


class ServiceType(Choice):
    
    register = Register({'application': Application, 'computer': Computer, 'vm': VM, 
			 'pod': Pod, 'container': Container, 'host': Host,
         'network_service': NetworkService, 'cloud': Cloud, 'network': Network, 'iot': IOT})
    #Il tipo Hostname è utilizzabile per reverse-dns

    def __init__(self, service_type):
        super().__init__(service_type)
