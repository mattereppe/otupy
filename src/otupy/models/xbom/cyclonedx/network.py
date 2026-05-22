from otupy.models.ctxd.network import Network

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert Network to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="network")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:network:id", value=self.id))
	if self.type is not None:
		type_value = self.get_subtype() if hasattr(self.type, 'getName') else str(self.type)
		properties.append(Property(name="otupy:network:type", value=type_value))
	
	return Service(
		name=self.name or "unknown",
		bom_ref=generate_bom_ref("network"),
		description=self.description,
		properties=properties
	)

Network.to_cyclonedx = to_cyclonedx
