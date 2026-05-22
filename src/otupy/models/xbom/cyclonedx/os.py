from otupy.models.ctxd.os import OS

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert OS to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type OPERATING_SYSTEM.
	"""
	properties = [
		Property(name="otupy:type", value="os")
	]
	# if self.id is not None:
	# 	properties.append(Property(name="otupy:os:id", value=self.id))
	if self.family is not None:
		properties.append(Property(name="otupy:os:family", value=self.family))
	if self.arch is not None:
		properties.append(Property(name="otupy:os:arch", value=self.arch))
	
	# Include nested components from ExecutionEnvironment
	
	return Component(
		name= "tmp",
		type=ComponentType.OPERATING_SYSTEM,
		bom_ref=generate_bom_ref("os"),
		version=self.version,
		# description=self.description,
		properties=properties
	)
