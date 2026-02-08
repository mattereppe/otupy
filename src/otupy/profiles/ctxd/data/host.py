from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy import Hostname

class Host(CTXDObject):
	""" Generic Host

		A Host is an electronic device designed to run a general-purpose operating system and application software.

		A Host will contain hardware peripherals like disks, network cards, CPUs, memory, GPUs, etc. The current 
		implementation only describe the overall host and does not consider its subsystems. 

		A Host will typically contain an execution environment (`ExecutionEnvironment`); 
		it could also be virtualized, giving rise	to the `VM` model.

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
			version: str = None):
	
		if host is not None:
			super().__init__(name=host.name, id=host.id, description=host.description)
			self.vendor = host.vendor
			self.model = host.model
			self.release = host.release
			self.serial = host.serial
			self.firmware = host.firmware
			self.version = host.version
			self.ports = host.ports
		else:
			super().__init__(name=name, id=id, description=description)
			self.vendor = vendor 
			self.model = model 
			self.release = release 
			self.serial = serial 
			self.firmware = firmware
			self.version = version
	
	def __repr__(self):
		return (f"Host({super().__repr__()}),"
					f"vendor='{self.vendor}'," 
					f"model='{self.model}'," 
					f"release='{self.release}'," 
					f"serial='{self.serial}'," 
					f"firmware='{self.firmware}'," 
					f"version='{self.version}'")
	
	def __str__(self):
		return __repr__(self)

