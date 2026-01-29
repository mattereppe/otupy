""" Mobile network

	Defines the main characteristics of a 5G network.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

class MobileNetwork(Map):
	""" Mobile 4/5G Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, mcc = str, mnc = str, region = int, set = int, 
			netv4addrs = ArrayOf(IPv4Net), netv6addrs = ArrayOf(IPv6Net))
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



