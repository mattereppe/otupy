""" Ethernet network

	Defines the main characteristics of an Ethernet network.
	Includes both virtual and physical infrastructures.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

class EthernetNetwork(Map):
	""" Ethernet Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(netv4nets = ArrayOf(IPv4Net), netv6nets = ArrayOf(IPv6Net))
	""" Field types
	
		This is the definition of the fields beard by the `Ethernet` network.
	"""



