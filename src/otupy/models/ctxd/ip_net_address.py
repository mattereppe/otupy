import ipaddress

from otupy import Choice, IPv4Net, IPv6Net, Register

class IPNetAddress(Choice):
	""" Define generic IP network address

		`IPNetAddress` can contain both an `IPv4Net` or an `IPv6Net`. It adds a higher
		level of abstraction to avoid keeping track of two kinds of addresses.
	"""
	register= Register({'ipv4': IPv4Net, 'ipv6': IPv6Net})

	def __init__(self, net_address):
		""" Initialize an IP address

			It automatically detects the type of Address and raise an exception if an
			invalid address is provided.

			:param net_address: The IP address provided as str, IPv4Addr, or IPv6Addr
		"""
		vers =  ipaddress.ip_network(net_address).version
		if vers == 4:
			super().__init__(IPv4Net(net_address))
		else:
			super().__init__(IPv6Net(net_address))
		
	def __str__(self):
		return str(self.getObj())

	def __repr__(self):
		return str(self.getObj())

