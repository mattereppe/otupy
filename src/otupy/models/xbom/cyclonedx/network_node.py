from otupy.models.ctxd.network_node import NetworkNode

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service | list[Property]: # type: ignore
	"""Convert NetworkNode to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service.
	"""
	properties = [
		Property(name="otupy:type", value="network_node")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:netnode:id", value=self.id))
	
	# Add interface properties
	if self.ifaces is not None:
		for i, iface in enumerate(self.ifaces):
			iface_props = iface.to_cyclonedx(prefix=f"otupy:netnode:iface:{i}")
			properties.extend(iface_props)
	
	return Service(
		name=self.description or "unknown", # TODO: give better names, the only ones available are PORTS
		bom_ref=generate_bom_ref("network_node"),
		description=self.description,
		properties=properties
	)

NetworkNode.to_cyclonedx = to_cyclonedx
