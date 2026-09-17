from otupy.models.ctxd.server import Server

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert Server to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type PLATFORM.
	"""
	properties = [
		Property(name="otupy:type", value="server")
	]
	
	return Component(
		name="server",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("server"),
		properties=properties
	)

Server.to_cyclonedx = to_cyclonedx
