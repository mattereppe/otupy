""" Tunnel link

	Abstract a tun link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf 
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress

class TunnelNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(server= str, nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param server: The server of the VPN
		:param nets: Network addesses used in this network
	"""

	def getNets(self):
		return self['nets']



