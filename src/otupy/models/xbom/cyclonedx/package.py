from otupy.models.ctxd.package import Package

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Package to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type LIBRARY (CycloneDX uses LIBRARY for packages).
	"""
	properties = [
		Property(name="otupy:type", value="package")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:package:id", value=self.id))
	if self.source is not None:
		properties.append(Property(name="otupy:package:source", value=str(self.source)))
	if self.pkg_type is not None:
		properties.append(Property(name="otupy:package:type", value=self.pkg_type))
	if self.arch is not None:
		properties.append(Property(name="otupy:package:arch", value=self.arch))

	return Component(
		name=self.name or "unknown",
		type=ComponentType.FILE,
		bom_ref=self.getId(),
		version=self.version,
		description=self.description,
		properties=properties
	)

Package.to_cyclonedx = to_cyclonedx
