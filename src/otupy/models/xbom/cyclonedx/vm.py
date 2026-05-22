from otupy.models.ctxd.vm import VM

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert VM to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type PLATFORM.
	"""
	properties = [
		Property(name="otupy:type", value="virtual_machine")
	]
	if self.hypervisor is not None:
		properties.append(Property(name="otupy:vm:hypervisor", value=self.hypervisor))
	if self.hypervisor_type is not None:
		ht_value = self.hypervisor_type.name if hasattr(self.hypervisor_type, 'name') else str(self.hypervisor_type)
		properties.append(Property(name="otupy:vm:hypervisor-type", value=ht_value))
	if self.image is not None:
		properties.append(Property(name="otupy:vm:image", value=self.image))
	
	return Component(
		name="vm",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("vm"),
		properties=properties
	)


VM.to_cyclonedx = to_cyclonedx
