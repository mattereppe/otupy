from otupy import  Record, ArrayOf
from otupy.types.base import Enumerated

class HyperVisorType(Enumerated):
	""" Type of hypervisor 

		Type1 (bare-metal) o Type2 (hosted)
	"""
	native = 1
	hosted = 2

class VM(Record):
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
			image:str = None):
		if(isinstance(vm, VM)):
			self.hypervisor = vm.hypervisor
			self.hypervisor_type = vm.hypervisor_type
			self.image = vm.image
		else:
			self.hypervisor = hypervisor 
			self.hypervisor_type = hypervisor_type 
			self.image = image 


	def __repr__(self):
		return (f"VM("
					 f"hypervisor={self.hypervisor},"
					 f"hypervisor_type={self.hypervisor_type}," 
	             f"image={self.image}")
	
	def __str__(self):
		return self.__repr__()

