import ipaddress
from typing import List

from otupy.types.base import Choice

from otupy.core.register import Register
from otupy.types.base import Record, ArrayOf
from otupy import MACAddr
from otupy.profiles.xbom.data.network_interface import IPAddress, IPInfo
from cyclonedx.model import Property
from otupy.types.data.ipv4_addr import IPv4Addr
from otupy.types.data.ipv6_addr import IPv6Addr

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

	def as_cyclonedx(self, prefix: str = "otupy:ipinfo") -> list:
		"""Convert IPInfo to CycloneDX properties format.
		
		Args:
			prefix: The prefix to use for property names.
		
		Returns:
			list: List of CycloneDX Property objects.
		"""
		properties = [
			Property(name=f"{prefix}:ip", value=str(self.ip)),
			Property(name=f"{prefix}:prefix", value=str(self.prefix))
		]
		if self.gw is not None:
			properties.append(Property(name=f"{prefix}:gateway", value=str(self.gw)))
		return properties


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

	def __init__(self, description=None, id=None, iface=None, mac=None, ips=None):
		if isinstance(description, Port):
			self.description = description.description
			self.id = description.id
			self.iface = description.iface
			self.mac = description.mac
			self.ips = description.ips
		else:
			self.description = str(description) if description is not None else None
			self.id = str(id) if id is not None else None
			self.iface = str(iface) if iface is not None else None
			self.mac = MACAddr(mac) if mac is not None else None
			self.ips = ips if ips is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Port(description={self.description}, id={self.id}, "
	             f"iface={self.iface}, mac={self.mac}, ips={self.ips})")
	
	def __str__(self):
		return self.__repr__()
	
	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")		
		if self.iface is not None and not isinstance(self.iface, str):
			raise TypeError(f"Expected 'iface' to be of type str, but got {type(self.iface)}")
		if self.mac is not None and not isinstance(self.mac, MACAddr):
			raise TypeError(f"Expected 'mac' to be of type MACAddr, but got {type(self.mac)}")
		if self.ips is not None and not issubclass(type(self.ips), list):
			raise TypeError(f"Expected 'ips' to be of type ArrayOf(IPInfo), but got {type(self.ips)}")

	def as_cyclonedx(self) -> List[Property]:
		"""Convert Port to CycloneDX properties format.
		
		Returns:
			List[Property]: List of CycloneDX Property objects.
		"""
		properties = []
		
		port_id = self.id if self.id is not None else "0"
		
		properties.append(Property(name="otupy:port:id", value=port_id))
		
		if self.description is not None:
			properties.append(Property(name=f"otupy:port:{port_id}:description", value=self.description))
		if self.iface is not None:
			properties.append(Property(name=f"otupy:port:{port_id}:iface", value=self.iface))
		if self.mac is not None:
			properties.append(Property(name=f"otupy:port:{port_id}:mac", value=str(self.mac)))
		if self.ips is not None:
			for i, ip_info in enumerate(self.ips):
				properties.append(Property(name=f"otupy:port:{port_id}:ip:{i}", value=str(ip_info.ip)))
				if ip_info.prefix is not None:
					properties.append(Property(name=f"otupy:port:{port_id}:ip:{i}:prefix", value=str(ip_info.prefix)))
				if ip_info.gw is not None:
					properties.append(Property(name=f"otupy:port:{port_id}:ip:{i}:gateway", value=str(ip_info.gw)))
		
		return properties

