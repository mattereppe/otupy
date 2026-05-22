from otupy.models.ctxd.cloud import Cloud

from cyclonedx.model import Property
from cyclonedx.model.contact import OrganizationalEntity
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref


def to_cyclonedx(self) -> Service:
	"""Convert Cloud to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="cloud")
	]
	if self.type is not None:
		properties.append(Property(name="otupy:cloud:type", value=self.get_subtype() if hasattr(self, 'get_subtype') else str(self.type)))
	if self.id is not None:
		properties.append(Property(name="otupy:cloud:id", value=self.id))
	
	provider = OrganizationalEntity(name=self.name) if self.name else None
	
	return Service(
		name=self.name or "unknown",
		bom_ref=generate_bom_ref("cloud"),
		description=self.description,
		provider=provider,
		properties=properties
	)

Cloud.to_cyclonedx = to_cyclonedx
