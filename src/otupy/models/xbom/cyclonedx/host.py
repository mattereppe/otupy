from otupy.models.ctxd.host import Host

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Host to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type PLATFORM.
	"""
	properties = [
		Property(name="otupy:type", value="host")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:host:id", value=self.id))
	if self.vendor is not None:
		properties.append(Property(name="otupy:host:vendor", value=self.vendor))
	if self.model is not None:
		properties.append(Property(name="otupy:host:model", value=self.model))
	if self.release is not None:
		properties.append(Property(name="otupy:host:release", value=self.release))
	if self.serial is not None:
		properties.append(Property(name="otupy:host:serial", value=self.serial))
	if self.firmware is not None:
		properties.append(Property(name="otupy:host:firmware", value=self.firmware))
	if self.version is not None:
		properties.append(Property(name="otupy:host:version", value=self.version))
	if self.type is not None:
		properties.append(Property(name="otupy:host:type", value=self.get_subtype() if hasattr(self.type, 'getName') else str(self.type)))
		
	return Component(
		name=self.name or "unknown",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("host"),
		description=self.description,
		properties=properties
	)

Host.to_cyclonedx = to_cyclonedx
