from otupy.types.base import  ArrayOf
from otupy.profiles.ctxd.data.host import Host
from otupy.types.base import Enumerated

class HyperVisorType(Enumerated):
	""" Type of hypervisor 

		Type1 (bare-metal) o Type2 (hosted)
	"""
	native = 1
	hosted = 2

class VM(Host):
	""" Virtual Machine

		A Virtual Machine is a virtualization environment that emulates a full computer hardware.
		It provides virtualized hardware as network interfaces, virtual CPUs, virtual RAM, and storage.
		Since this model shares most of the components with any other network host, it will inherit from
		the `Host` abstraction and will extend with additional information for virtualization.
	"""
	hypervisor: str = None
	""" Hypervisor name (e.g., QEMU, XEN, ...) """
	hypervisor_type: HyperVisorType = None
	""" Type of the hypervisor: native (bare-metal) or hosted """
	image: str = None
	""" Software image loaded in the VM """


	def __init__(self, 
			vm: object = None,
			hypervisor: str = None,
			hypervisor_type: HyperVisorType=None, 
			image:str = None, 
			**kwargs):
		if(isinstance(vm, VM)):
			super().__init__(vm)
			self.hypervisor = vm.hypervisor
			self.hypervisor_type = vm.hypervisor_type
			self.image = vm.image
		else:
			super().__init__(**kwargs)
			self.hypervisor = hypervisor 
			self.hypervisor_type = hypervisor_type 
			self.image = image 


	@staticmethod
	def getType():
		return "vm"

	def __repr__(self):
		return (f"VM("
					 f"{super().__repr__()},"
					 f"hypervisor={self.hypervisor},"
					 f"hypervisor_type={self.hypervisor_type}," 
	             f"image={self.image}")
	
	def __str__(self):
		return self.__repr__()

	def validate_fields(self):
		if self.hypervisor is not None and not isinstance(self.hypervisor, str):
			raise TypeError(f"Expected 'hypervisor' to be of type {str}, but got {type(self.hypervisor)}")
		if self.hypervisor_type is not None and not isinstance(self.hypervisor_type, str):
			raise TypeError(f"Expected 'hypervisor_type' to be of type {HyperVisorType}, but got {type(self.hypervisor_type)}")
		if self.image is not None and not isinstance(self.image, str):
			raise TypeError(f"Expected 'image' to be of type {str}, but got {type(self.image)}")
