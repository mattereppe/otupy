from typing import TYPE_CHECKING
from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy import Hostname
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

if TYPE_CHECKING:
	from otupy.profiles.xbom.data.host_type import HostType

class Host(XBOMObject):
	""" Generic Host

		A Host is an environment that provides resources to an ``ExecutionEnvironment``. The more common way to 
	  	understand a host is an electronic device designed to run a general-purpose operating system 
		and application software.

		A Host will contain hardware peripherals like disks, network cards, CPUs, memory, GPUs, etc. However,
		these resources may be both physical and virtualised, providing a broad range different ``Hosts``. 
		A ``Host`` could be a server, an IoT device, a Virtual Machine, a Kubernetes Pod... everything is designed
		to host an ExecutionEnvironment. However, the current 
		implementation only describes the overall host and does not consider its subsystems. 

		The combination of ``Host``s and ``ExecutionEnvironment`` will create a recursive hierarchy of dependencies,
		where ``ExecutionEnvironment``s are contained in ``Host``s, and ``Host``s may be implemented in 
		``ExecutionEnvironments``. 

	"""

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
	type: 'HostType' = None
	""" Specific device type (including virtual and physical devices """

	def __init__(self, 
			host:object = None,
			name:Hostname = None, 
			id:str = None, 
			description:str = None, 
			vendor: str = None,
			model: str = None,
			release: str = None,
			serial: str = None,
			firmware: str = None,
			version: str = None,
			type: 'HostType' = None):
	
		if host is not None:
			super().__init__(name=host.name, id=host.id, description=host.description)
			self.vendor = host.vendor
			self.model = host.model
			self.release = host.release
			self.serial = host.serial
			self.firmware = host.firmware
			self.version = host.version
			self.type = host.type
		else:
			super().__init__(name=name, id=id, description=description)
			self.vendor = vendor 
			self.model = model 
			self.release = release 
			self.serial = serial 
			self.firmware = firmware
			self.version = version
			self.type = type
	
	def __repr__(self):
		return (f"Host({super().__repr__()}),"
					f"vendor='{self.vendor}'," 
					f"model='{self.model}'," 
					f"release='{self.release}'," 
					f"serial='{self.serial}'," 
					f"firmware='{self.firmware}'," 
					f"version='{self.version}',"
					f"type='{self.type}')")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Host to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		properties = [
			Property(name="otupy:type", value="host")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:host:id", value=self.id))
		if self.vendor is not None:
			properties.append(Property(name="otupy:host:vendor", value=self.vendor))
		if self.model is not None:
			properties.append(Property(name="otupy:host:model", value=self.model))
		if self.release is not None:
			properties.append(Property(name="otupy:host:release", value=self.release))
		if self.serial is not None:
			properties.append(Property(name="otupy:host:serial", value=self.serial))
		if self.firmware is not None:
			properties.append(Property(name="otupy:host:firmware", value=self.firmware))
		if self.version is not None:
			properties.append(Property(name="otupy:host:version", value=self.version))
		if self.type is not None:
			properties.append(Property(name="otupy:host:type", value=self.type.get_type_name(type(self.type.getObj())) if self.type is not None else "unknown"))
			
		return Component(
			name=self.name or "unknown",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("host"),
			description=self.description,
			properties=properties
		)
