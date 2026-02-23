from otupy import Choice, Register
from otupy.profiles.xbom.data.network_router import Router
from otupy.profiles.xbom.data.network_nat import NAT

#ATTENTION!! THIS IS ONLY PARTIALLY DEFINED!!!
class NetworkFunctionType(Choice):
	""" Network function type

		The network function type carries different configuration parameters, depending on the specific network 
		function.

		WARNING: This definition is currently partial, since it does not include all possible functions.
	"""

	register = Register({'router': Router, 'vpn': str, 'nat': NAT})

	def __init__(self, type):
		if(isinstance(type, NetworkFunctionType)):
			super().__init__(type.getObj())
		else:
			super().__init__(type)
