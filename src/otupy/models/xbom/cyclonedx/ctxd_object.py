from otupy.models.ctxd import CTXDObject

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref


def to_cyclonedx(self) -> Component:
	"""Convert XBOMObject to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type PLATFORM.
	"""
	properties = [
		Property(name="otupy:type", value="xbom_object")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:xbom_object:id", value=self.id))

	return Component(
		name=self.name or "unknown",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("xbom_object"),
		description=self.description,
		properties=properties
	)

CTXDObject.to_cyclonedx = to_cyclonedx
