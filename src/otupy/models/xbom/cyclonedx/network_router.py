""" Network router

	Defines the main characteristics of an IP router.
"""

from otupy.models.ctxd.network_router import Router

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert Router to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="router")
	]
	
	routes = self.get('routes')
	if routes is not None:
		properties.append(Property(name="otupy:router:routes", value=routes))
	
	return Service(
		name="router",
		bom_ref=generate_bom_ref("router"),
		properties=properties
	)

Router.to_cyclonedx = to_cyclonedx
