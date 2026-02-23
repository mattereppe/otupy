from typing import List

from otupy.types.base import Record, ArrayOf
from otupy import MACAddr
from otupy.profiles.xbom.data.network_interface import IPAddress, IPInfo
from cyclonedx.model import Property

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
	""" MAC or similar L2 addresses associated to this port """
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

