""" Veth pseudo-network

	Abstract a veth link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf 
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress

class VEthNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(peers= tuple, nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param peers: A couple of interfaces names
		:param nets: Network addesses used in this network
	"""



