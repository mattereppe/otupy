""" Mobile network

	Defines the main characteristics of a 5G network.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net
from otupy.models.ctxd.ip_network import IPNetwork
from otupy.models.ctxd.ip_net_address import IPNetAddress

class MobileNetwork(Map):
	""" Mobile 4/5G Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, mcc = str, mnc = str, region = int, sst = int, 
			nets = ArrayOf(IPNetAddress))

	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param name: mnemonic identifier for the network
		:param mnc: Mobile Network Code
		:param mcc: Mobile Country Code
		:param region: Region 
		:param sst: TBD
		:param nets: Network addesses used in this network
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



