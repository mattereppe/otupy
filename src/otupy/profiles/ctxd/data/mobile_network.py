""" Mobile network

	Defines the main characteristics of a 5G network.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net
from otupy.profiles.ctxd.data.ip_network import IPNetwork
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress

class MobileNetwork(Map):
	""" Mobile 4/5G Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, mcc = str, mnc = str, region = int, set = int, 
			nets = ArrayOf(IPNetAddress))

	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param name: mnemonic identifier for the network
		:param mmc: Mobile Network Code
		:param mnc: Mobile Country Code
		:param region: Region 
		:param int: TBD
		:param netv4addrs: Network addesses used in this network
		:param netv6addrs: Network IPv6 addresses used in this network
	"""


	def getNets(self):
		nets = []
		if 'mcc' in self:
			nets.append("mcc:"+self['mcc'])
		if 'mnc' in self:
			nets.append("mnc:"+self['vlan_id'])
		if 'nets' in self:
			for n in self['nets']:
				nets.append(n)		
		return nets



