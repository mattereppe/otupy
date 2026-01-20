from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.computer import Computer
from otupy.profiles.xbom.data.web_service import WebService
from otupy.types.base import Choice
from otupy.core.extensions import Register


class ServiceType(Choice):
    
    register = Register({'application': Application, 'computer': Computer, 'vm': VM, 'pod': Pod, 'container': Container, 'web_service': WebService,
                         'cloud': Cloud, 'network': Network, 'iot': IOT})
    #Il tipo Hostname è utilizzabile per reverse-dns

    def __init__(self, service_type):
        super().__init__(service_type)
