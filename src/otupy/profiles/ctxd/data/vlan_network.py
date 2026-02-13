""" Virtual LAN network

	Defines the main characteristics of a  VLAN
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress


class VLANNetwork(Map):
	""" Virtual Local Area Network 

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, vlan_id = str, type = str,
			nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param name: mnemonic identifier for the network
		:param vlan_id: Identifier for this VLAN segment
		:param type: VLAN protocol (e.g., 802.1Q)
		:param netv4nets: Network addesses used in this network
		:param netv6nets: Network IPv6 addresses used in this network
	"""



