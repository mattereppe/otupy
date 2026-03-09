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
	
	register = Register({'app': Application, 'execenv': ExecutionEnvironment, 
		'host': Host, 'netnode': NetworkNode,
		 'api': API, 'cloud': Cloud, 'network': Network, 'netfun': NetworkFunction,
		 'os': OS, 'container': Container, 'pod': Pod, 'iot': IOT,
		 'vm': VM, 'server': Server, 'webservice': WebService})
	#Il tipo Hostname è utilizzabile per reverse-dns
	
	def __init__(self, service_type):
		super().__init__(service_type)
	
	@staticmethod
	def get_type_name(service_type: object):
		""" Get the name associated to a given class
		    
			If the class is not registered, None is returned.
			
			@:param service_type: The class to get the name for.
			@:return: The string used to register the class.
		"""
		return ServiceType.register.getName(service_type)
