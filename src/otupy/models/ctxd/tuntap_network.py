""" Tun/Tap link

	Abstract the presence of an application behind a Tun/Tap network
"""

from otupy import Map, ArrayOf 
from otupy.models.ctxd.ip_net_address import IPNetAddress

class TunTapNetwork(Map):
	""" Tun/Tap network

		A lightweight indication of application-defined network
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(app= str, nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param app: The application that implements the network
		:param nets: Network addesses used in this network
	"""

	def getNets(self):
		return self['nets']



