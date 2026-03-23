""" Veth pseudo-network

	Abstract a veth link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf , Array
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress

class VEthPeer(Array):
	""" VEth network interface peers

		A tuple would be more appropriate to store a pair of information
		(interface idx, namespace), but there is not such base type
		in the OpenC2 language. An Array if the most fitting data type.
	"""
	pass


class VEthNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(peers= ArrayOf(VEthPeer), nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param peers: A couple of interfaces names
		:param nets: Network addesses used in this network
	"""

	def getNets(self):
		return self['nets']



