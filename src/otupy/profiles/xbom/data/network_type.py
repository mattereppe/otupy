from otupy.types.base import Choice
from otupy.core.register import Register
from otupy.profiles.xbom.data.ethernet_network import EthernetNetwork
from otupy.profiles.xbom.data.mobile_network import MobileNetwork
from otupy.profiles.xbom.data.vlan_network import VLANNetwork
from otupy.profiles.xbom.data.ip_network import IPNetwork
from otupy.profiles.xbom.data.veth_network import VEthNetwork
from otupy.profiles.xbom.data.tunnel_network import TunnelNetwork
from otupy.profiles.xbom.data.vxlan_network import VXLANNetwork

#ATTENTION!! THIS IS ONLY PARTIALLY DEFINED!!!
class NetworkType(Choice):
	""" Network type

		The network type carries different configuration parameters, depending on the specific network 
		technology.

		WARNING: This definition is currently partial, since it does not include network parameters for
		most of network types. When the network is defined as str, it returns something like: "ethernet": "ethernet".
	"""

	register = Register({'ip': IPNetwork, 'eth': EthernetNetwork, '802.11': str, '802.15': str, 'zigbee': str, 
			'vlan': VLANNetwork, 'tun': TunnelNetwork, 'veth': VEthNetwork, 'vxlan': VXLANNetwork,
			'vpn': str, 'lorawan': str, 'wan': str, '5G': MobileNetwork})

	def __init__(self, type):
		if(isinstance(type, NetworkType)):
			super().__init__(type.obj)
		else:
			super().__init__(type)

	@staticmethod
	def get_type_name(net_type: object):
		""" Get the name associated to a given class
		    
			If the class is not registered, None is returned.
			
			@:param service_type: The class to get the name for.
			@:return: The string used to register the class.
		"""
		return ExecutionEnvironmentType.register.getName(net_type)
