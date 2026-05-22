from otupy.models.ctxd import Application

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref


def to_cyclonedx(self) -> Component:
	"""Convert Application to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type APPLICATION.
	"""
	properties = [
		Property(name="otupy:type", value="application")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:application:id", value=self.id))
	if self.owner is not None:
		properties.append(Property(name="otupy:application:owner", value=self.owner))
	if self.app_type is not None:
		properties.append(Property(name="otupy:application:type", value=self.get_subtype() if hasattr(self, 'get_subtype') else str(self.app_type)))
	
	return Component(
		name=self.name or "unknown",
		type=ComponentType.APPLICATION,
		version=self.version,
		description=self.description,
		properties=properties
	)

Application.to_cyclonedx = to_cyclonedx
