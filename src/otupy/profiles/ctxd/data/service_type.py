from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.network_function import NetworkFunction
from otupy.profiles.ctxd.data.network_node import NetworkNode
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.api import API
from otupy.types.base import Choice
from otupy.core.extensions import Register


# TODO: Add auto-registration of the classes with a decorator to avoid missing them in the list below
class ServiceType(Choice):
	
	register = Register({'app': Application, 'execenv': ExecutionEnvironment, 
		'host': Host, 'netnode': NetworkNode,
		 'api': API, 'cloud': Cloud, 'network': Network, 'netfun': NetworkFunction})
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
