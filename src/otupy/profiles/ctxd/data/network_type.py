from otupy.types.base import Choice
from otupy.core.register import Register
from otupy.profiles.ctxd.data.ethernet_network import EthernetNetwork
from otupy.profiles.ctxd.data.mobile_network import MobileNetwork
from otupy.profiles.ctxd.data.vlan_network import VLANNetwork

#ATTENTION!! THIS IS ONLY PARTIALLY DEFINED!!!
class NetworkType(Choice):
	""" Network type

		The network type carries different configuration parameters, depending on the specific network 
		technology.

		WARNING: This definition is currently partially, since it does not include network paramters for
		most of network types. When the network is defined as str, it returns something like: "ethernet": "ethernet".
	"""

	register = Register({'ethernet': EthernetNetwork, '802.11': str, '802.15': str, 'zigbee': str, 
			'vlan': VLANNetwork, 'vpn': str, 'lorawan': str, 'wan': str, '5G': MobileNetwork})

	def __init__(self, type):
		if(isinstance(type, NetworkType)):
			super().__init__(type.obj)
		else:
			super().__init__(type)
