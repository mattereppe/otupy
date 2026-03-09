from otupy.types.base import Enumerated
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record

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

	def __repr__(self):
		return (f"VM("
					 f"{super().__repr__()},"
					 f"hypervisor={self.hypervisor},"
					 f"hypervisor_type={self.hypervisor_type}," 
	             f"image={self.image}")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert VM to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		properties = [
			Property(name="otupy:type", value="virtual_machine")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:vm:id", value=self.id))
		if self.hypervisor is not None:
			properties.append(Property(name="otupy:vm:hypervisor", value=self.hypervisor))
		if self.hypervisor_type is not None:
			ht_value = self.hypervisor_type.name if hasattr(self.hypervisor_type, 'name') else str(self.hypervisor_type)
			properties.append(Property(name="otupy:vm:hypervisor-type", value=ht_value))
		if self.image is not None:
			properties.append(Property(name="otupy:vm:image", value=self.image))
		if self.vendor is not None:
			properties.append(Property(name="otupy:vm:vendor", value=self.vendor))
		if self.model is not None:
			properties.append(Property(name="otupy:vm:model", value=self.model))
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("vm"),
			description=self.description,
			properties=properties
		)
