from otupy.models.ctxd.pod import Pod

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Pod to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component representation.
	"""
	properties = [
		Property(name="otupy:type", value="pod")
	]
	if self.namespace is not None:
		properties.append(Property(name="otupy:pod:namespace", value=self.namespace))
	
	# Generate a unique bom_ref using centralized generator
	bom_ref = generate_bom_ref("pod")
	
	return Component(
		name="pod",
		type=ComponentType.PLATFORM,
		bom_ref=bom_ref,
		properties=properties
	)	

Pod.to_cyclonedx = to_cyclonedx
