from otupy import Choice, Register
from otupy.models.ctxd.network_router import Router
from otupy.models.ctxd.network_bridge import Bridge
from otupy.models.ctxd.network_nat import NAT
from otupy.models.ctxd.network_firewall import Firewall

#ATTENTION!! THIS IS ONLY PARTIALLY DEFINED!!!
class NetworkFunctionType(Choice):
	""" Network function type

		The network function type carries different configuration parameters, depending on the specific network 
		function.

		WARNING: This definition is currently partially, since it does not include all possible functions.
	"""

	register = Register({'router': Router, 'vpn': str, 'nat': NAT, 'bridge': Bridge, 'fw': Firewall})

	def __init__(self, type):
		if(isinstance(type, NetworkFunctionType)):
			super().__init__(type.getObj())
		else:
			super().__init__(type)

	@staticmethod
	def get_type_name(net_fun_type: object):
		""" Get the name associated to a given class
		    
			If the class is not registered, None is returned.
			
			@:param service_type: The class to get the name for.
			@:return: The string used to register the class.
		"""
		return NetworkFunctionType.register.getName(net_fun_type)
