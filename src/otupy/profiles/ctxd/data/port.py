from otupy.types.base import Record, ArrayOf
from otupy.types.data import IPv4Addr
from otupy.profiles.ctxd.data.os import OS

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
	addresses: ArrayOf(IPv4Addr) = None
	""" Hostname managing the Container"""
	gateway: IPv4Addr = None
	""" Operating System of the Container """

	def __init__(self, description = None, id = None, iface = None, addresses = None, gateway = None):
		if isinstance(description, Port):
			self.description = description.description
			self.id = description.id
			self.iface = description.iface
			self.addresses = description.addresses
			self.gateway = description.gateway
		else:
			self.description = str(description) if description is not None else None
			self.id = str(id) if id is not None else None
			self.iface = str(iface) if iface is not None else None
			if addresses is not None:
				self.addresses = ArrayOf(IPv4Addr)()
				for address in addresses:
					self.addresses.append(IPv4Addr(address))
			self.gateway = gateway if gateway is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Port(description={self.description}, id={self.id}, "
	             f"iface={self.iface}, addresses={self.addresses},gateway={self.gateway})")
	
	def __str__(self):
		return f"Port(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"iface={self.iface}, " \
				f"addresses={self.addresses}, " \
	            f"gateway={self.gateway})"
	
	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")		
		if self.iface is not None and not isinstance(self.iface, str):
			raise TypeError(f"Expected 'hostname' to be of type {str}, but got {type(self.hostname)}")
		if self.addresses is not None and not issubclass(type(self.addresses), list):
			print("Addresses: ", type(self.addresses[0]))
			raise TypeError(f"Expected 'addresses' to be of type {ArrayOf(IPv4Addr)}, but got {type(self.addresses)}")	
		if self.gateway is not None and not isinstance(self.gateway, ArrayOf(IPv4Addr)):
			raise TypeError(f"Expected 'os' to be of type {gateway}, but got {type(self.gateway)}")

