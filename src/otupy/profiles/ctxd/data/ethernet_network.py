""" Ethernet network

	Defines the main characteristics of an Ethernet network.
	Includes both virtual and physical infrastructures.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net 
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress

class EthernetNetwork(Map):
	""" Ethernet Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(nets = ArrayOf(IPNetAddress), netv4nets = ArrayOf(IPv4Net), netv6nets = ArrayOf(IPv6Net))
	""" Field types
	
		This is the definition of the fields beard by the `Ethernet` network.
	"""

	def getNets(self):
		return self['nets']


