""" Virtual eXtensible LAN network

	Defines the main characteristics of a  VXLAN
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress


class VXLANNetwork(Map):
	""" Virtual eXtensible "Local" Area Network 

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(vni = str, port = str,
			nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param vni: Identifier for this VLAN segment
		:param port: UDP port 
		:param nets: Network addesses used in this network
	"""



