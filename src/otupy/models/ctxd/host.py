from otupy.models.ctxd.ctxd_object import CTXDObject
from otupy.models.ctxd.host_type import HostType
from otupy import Hostname

class Host(CTXDObject):
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
	type: HostType = None
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
			type: HostType = None):
	
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
	
	def get_subtype(self):
		return self.type.getName()

	def __repr__(self):
		return (f"Host("
					f"{super().__repr__()},"
					f"vendor='{self.vendor}'," 
					f"model='{self.model}'," 
					f"release='{self.release}'," 
					f"serial='{self.serial}'," 
					f"firmware='{self.firmware}'," 
					f"version='{self.version}',"
					f"type='{self.type.getObj().__repr__()}')")
	
	def __str__(self):
		return self.__repr__()

