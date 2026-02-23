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
			prefix = 32 if type(self.ip.getObj()) == IPv4Addr else 128

		if (int(prefix) < 0) or (type(self.ip.getObj()) == IPv4Addr and  int(prefix) > 32) or \
			(type(self.ip.getObj()) == IPv6Addr and int(prefix) > 128):
			raise ipaddress.NetmaskValueError("Wrong prefix length: "+str(prefix))
		self.prefix = int(prefix)
		self.gw = IPAddress(gw) if gw is not None else None

		if self.gw is not None:
			assert type(self.ip) == type(self.gw)

	def __str__(self):
		return f"IPInfo(addr: {self.ip}/{self.prefix}, gw: {self.gw}"

	def __repr__(self):
		return f"IPInfo(addr: {self.ip}/{self.prefix}, gw: {self.gw}"

class Port(Record):
	"""Port
    it is the description of a network interface
	"""
	description: str = None
	""" Generic description of the Port """
	id: str = None
	""" ID of the Port """
	iface: str = None
	""" Name of the network interface (OS dependent)"""
	mac: MACAddr = None
	""" MAC or similar L2 addresses associated to this port (not implemented) """
	ips: ArrayOf(IPInfo) = None
	""" List of IP addresses/gateways associated to the interface """

	def __init__(self, port = None, description = None, id = None, iface = None, mac = None, ips = None):
		if port is not None:
			self.description = port.description
			self.id = port.id
			self.iface = port.iface
			self.mac = port.mac
			self.ips = port.ips
		else:
			self.description = str(description) 
			self.id = str(id) 
			self.iface = str(iface) 
			self.mac = MACAddr(mac) if mac is not None else None
			self.ips = ips 
		self.validate_fields()

	def __repr__(self):
		return (f"Port(description={self.description}, id={self.id}, iface={self.iface}, ips={self.ips})") 
	
	def __str__(self):
		return self.__repr__()
	
	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")		
		if self.iface is not None and not isinstance(self.iface, str):
			raise TypeError(f"Expected 'hostname' to be of type {str}, but got {type(self.hostname)}")
		if self.ips is not None and not issubclass(type(self.ips), list):
			raise TypeError(f"Expected 'ips' to be of type {ArrayOf(IPInfo)}, but got {type(self.ips)}")	

