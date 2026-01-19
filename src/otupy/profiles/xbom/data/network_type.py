from otupy.types.base import Choice
from otupy.core.register import Register

#ATTENTION!! THIS IS NOT THE DEFINITION OF THE CTXD SPECIFICATION 
class NetworkType(Choice):
	""" Network type

		The network type carries different configuration parameters, depending on the specific network 
		technology.

		WARNING: This definition is currently wrong, since it does not include network paramters.
		It returns something like: "ethernet": "ethernet".
	"""

	register = Register({'ethernet': str, '802.11': str, '802.15': str, 'zigbee': str, 'vlan': str, 'vpn': str, 'lorawan': str, 'wan': str})

	def __init__(self, type):
		if(isinstance(type, NetworkType)):
			super().__init__(type.obj)
		else:
			super().__init__(type)
