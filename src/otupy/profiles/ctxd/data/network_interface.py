import ipaddress

from otupy.types.base import Record, ArrayOf, Choice 
from otupy.types.data import IPv4Addr, IPv6Addr
from otupy import MACAddr
from otupy.core.extensions import Register
from otupy.profiles.ctxd.data.os import OS

class IPAddress(Choice):
	""" Define generic IP address

		`IPAddress` can contain both an `IPv4Addr` or an `IPv6Addr`. It adds a higher
		level of abstraction to avoid keeping track of two kinds of addresses.
	"""
	register= Register({'ipv4': IPv4Addr, 'ipv6': IPv6Addr})

	def __init__(self, address):
		""" Initialize an IP address

			It automatically detects the type of Address and raise an exception if an
			invalid address is provided.

			:param address: The IP address provided as str, IPv4Addr, or IPv6Addr
		"""
		vers =  ipaddress.ip_address(address).version
		if vers == 4:
			super().__init__(IPv4Addr(address))
		else:
			super().__init__(IPv6Addr(address))
		
	def __str__(self):
		return str(self.getObj())

	def __repr__(self):
		return str(self.getObj())

class IPInfo(Record):
	""" IP address and gateway information

		Packs together IP addressing informatin, including netmask and gateway
	"""
	ip: IPAddress = None
	""" IP address """
	prefix: int = None
	""" Prefix to identify the netmask """
	gw: IPAddress = None
	""" Default gateway """

	def __init__(self, ip: IPAddress, prefix: int = None, gw: IPAddress = None):
		self.ip = IPAddress(ip)
		if prefix is None:
			prefix = 32 if type(self.ip.getObj()) == IPv4Addr else 64

		if (int(prefix) < 0) or (type(self.ip.getObj()) == IPv4Addr and  int(prefix) > 32) or \
			(type(self.ip.getObj()) == IPv6Addr and int(prefix) > 64):
			raise ipaddress.NetmaskValueError("Wrong prefix length: "+str(prefix))
		self.prefix = int(prefix)
		self.gw = IPAddress(gw) if gw is not None else None

		if self.gw is not None:
			assert type(self.ip) == type(self.gw)

	def __str__(self):
		return f"IPInfo(addr: {self.ip}/{self.prefix}, gw: {self.gw}"

	def __repr__(self):
		return f"IPInfo(addr: {self.ip}/{self.prefix}, gw: {self.gw}"

class NetworkInterface(Record):
	""" Network Interface 

    	This object describes a network interface in general terms
	"""
	description: str = None
	""" Generic description of the interface (rarely available) """
	id: str = None
	""" ID of the interface (use iface index for Execution Environments and other id for cloud systems) """
	iface: str = None
	""" Name of the network interface (OS dependent)"""
	mac: MACAddr = None
	""" MAC or similar L2 addresses associated to this port (not implemented) """
	ips: ArrayOf(IPInfo) = None
	""" List of IP addresses/gateways associated to the interface """

	def __init__(self, interface = None, description = None, id = None, iface = None, ips = None):
		if isinstance(interface, NetworkInterface):
			self.description = interface.description
			self.id = interface.id
			self.iface = interface.iface
			self.ips = interface.ips
		else:
			self.description = str(description) if description is not None else None
			self.id = str(id) if id is not None else None
			self.iface = str(iface) if iface is not None else None
			self.ips = ips if ips is not None else None

	def __repr__(self):
		return (f"Port(description={self.description}, id={self.id}, iface={self.iface}, ips={self.ips})") 
	
	def __str__(self):
		return f"NetworkInterface(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"iface={self.iface}, " \
					f"ips={self.ips}" 

