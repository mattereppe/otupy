from otupy.models.ctxd.library import Library

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Library to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type LIBRARY.
	"""
	properties = [
		Property(name="otupy:type", value="library")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:library:id", value=self.id))
	if self.source is not None:
		properties.append(Property(name="otupy:library:source", value=str(self.source)))
	if self.lib_type is not None:
		properties.append(Property(name="otupy:library:type", value=self.lib_type))

	return Component(
		name=self.name or "unknown",
		type=ComponentType.LIBRARY,
		bom_ref=generate_bom_ref("library"),
		version=self.version,
		description=self.description,
		properties=properties
	)

Library.to_cyclonedx = to_cyclonedx
