from otupy.models.ctxd.endpoint import Endpoint

from cyclonedx.model import Property
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self, prefix: str = "otupy:endpoint") -> list:
	"""Convert Endpoint to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		list: List of CycloneDX Property objects.
	"""
	properties = []
	
	if self.endpoint_type is not None:
		properties.append(Property(name=f"{prefix}:type", value=self.endpoint_type))
	if self.transport is not None:
		properties.append(Property(name=f"{prefix}:transport", value=self.transport))
	if self.transfer is not None:
		properties.append(Property(name=f"{prefix}:transfer", value=self.transfer))
	if self.encoding is not None:
		properties.append(Property(name=f"{prefix}:encoding", value=self.encoding))
	if self.uri is not None:
		properties.append(Property(name=f"{prefix}:uri", value=self.uri))
	if self.provider is not None:
		properties.append(Property(name=f"{prefix}:provider", value=self.provider))
	if self.description is not None:
		properties.append(Property(name=f"{prefix}:description", value=self.description))
	
	return properties

Endpoint.to_cyclonedx = to_cyclonedx
