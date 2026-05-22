from otupy.models.ctxd.container import Container

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Container to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type CONTAINER.
	"""
	properties = [
		Property(name="otupy:type", value="container")
	]
	# if self.id is not None:
	# 	properties.append(Property(name="otupy:container:id", value=self.id))
	if self.namespace is not None:
		properties.append(Property(name="otupy:container:namespace", value=self.namespace))
	if self.status is not None:
		properties.append(Property(name="otupy:container:status", value=self.status))
	if self.image is not None:
		properties.append(Property(name="otupy:container:image", value=self.image))
	
	return Component(
		name="tmp",
		type=ComponentType.CONTAINER,
		properties=properties
	)

Container.to_cyclonedx = to_cyclonedx
