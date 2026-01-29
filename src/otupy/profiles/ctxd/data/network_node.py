from otupy.types.base import Record
from otupy.types.data.hostname import  Hostname

from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.port import Port

class NetworkNode(Record):
	""" Generic network node

		A `NetworkNode` is any kind of entity attached to the network. The scope includes both network
		equipment (routers, switches, access points) and hosts (computers attached to a network). .
		A `NetworkNode` has one or more network ports, which one with network identifiers specific to the
		implemented protocols (e.g., MAC addresses for Ethernet, IP addresses for IP).

		The `NetworkNode` represents a base class to derive more specific classes for network equipment and
		hosts, hosting the common network-related characteristics (namely, network ports). It can be used alone
		when it is a subsystem inside a bigger system, for instance a Linux network namespace, or when the 
		underlying implementation is not known (for instance, a router which concrete implementation is not know).

	"""
	name: Hostname = None
	""" Network name of the host (preferably a FQDN) """
	id: str = None
	""" ID of the node, preferably globally unique """
	description: str = None
	""" Generic description of the node (including its role) """
	vendor: str = None
	""" Vendor name """
	model: str = None
	""" Model identifier """
	release: str = None
	""" Release identifier """
	serial: str = None
	""" Serial number of the specific device """
	firmware: str = None
	""" Name of the firmware (e.g., BIOS, UEFI, iOS) """
	version: str = None
	""" Firmware version/release """
	ports: ArrayOf(Port) = None
	""" Network interfaces with addresses"""


	def __init__(self, 
			name:Hostname = None, 
			id:str = None, 
			description:str = None, 
			vendor: str = None,
			model: str = None,
			release: str = None,
			serial: str = None,
			firmware: str = None,
			version: str = None,
			ports:ArrayOf(Port) = None):
	
		if(isinstance(name, NetworkNode)):
			self.name = name.name
			self.id = name.id
			self.description = name.description
			self.vendor = name.vendor
			self.model = name.model
			self.release = name.release
			self.serial = name.serial
			self.firmware = name.firmware
			self.version = name.version
			self.ports = name.ports
		else:
			self.name = name if name is not None else None
			self.id = id if id is not None else None
			self.description = description if description is not None else None
			self.vendor = vendor if vendor is not None else None
			self.model = model if model is not None else None
			self.release = release if release is not None else None
			self.serial = serial if serial is not None else None
			self.firmware = firmware if firmware is not None else None
			self.version = version if version is not None else None
			if ports is not None:
				self.ports = ArrayOf(Port)()
				for port in ports:
					if isinstance(port, dict):
						self.ports.append(Port(**port))
					else:
						self.ports.append(Port(port))
			else:
				self.ports = None
		self.validate_fields()

	def __repr__(self):
		return (f"NetworkNode("
	            f"name='{self.name}',"
					f"id={self.id}, "
					f"description='{self.description}'," 
					f"vendor='{self.vendor}'," 
					f"model='{self.model}'," 
					f"release='{self.release}'," 
					f"serial='{self.serial}'," 
					f"firmware='{self.firmware}'," 
					f"version='{self.version}'," 
					f"ports={self.ports})")
	
	def __str__(self):
		return self.__repr__()

	def validate_fields(self):
		if self.description is not None and not (isinstance(self.description, str) or isinstance(self.description, VM)):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.name is not None and not isinstance(self.name, Hostname):
			raise TypeError(f"Expected 'name' to be of type Hostname, but got {type(self.name)}")
		if self.vendor is not None and not isinstance(self.vendor, str):
			raise TypeError(f"Expected 'vendor' to be of type str, but got {type(self.vendor)}")
		if self.model is not None and not isinstance(self.model, str):
			raise TypeError(f"Expected 'model' to be of type str, but got {type(self.id)}")
		if self.release is not None and not isinstance(self.release, str):
			raise TypeError(f"Expected 'release' to be of type str, but got {type(self.release)}")
		if self.serial is not None and not isinstance(self.serial, str):
			raise TypeError(f"Expected 'serial' to be of type str, but got {type(self.serial)}")
		if self.firmware is not None and not isinstance(self.firmware, str):
			raise TypeError(f"Expected 'firmware' to be of type str, but got {type(self.firmware)}")
		if self.version is not None and not isinstance(self.version, str):
			raise TypeError(f"Expected 'version' to be of type str, but got {type(self.version)}")
		if self.ports is not None and not issubclass(type(self.ports), list):
			raise TypeError(f"Expected 'ports' to be of type {ArrayOf(Port)}, but got {type(self.ports)}")	


