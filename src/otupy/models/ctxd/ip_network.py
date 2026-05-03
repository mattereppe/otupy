""" Generic IP network

	Defines the main characteristics of a generic IP network.
	This is expected to be used when no information about the concrete implementation of
	the underlying network is available.
"""

from otupy import Map, ArrayOf
from otupy.models.ctxd.ip_net_address import IPNetAddress

class IPNetwork(Map):
	""" Ethernet Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the  IP network.
	"""

	def getNets(self):
		return self['nets']


