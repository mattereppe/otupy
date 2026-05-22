from otupy.models.ctxd.web_service import WebService

from cyclonedx.model import Property, XsUri
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert WebService to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="web_service")
	]
	# if self.server is not None:
	# 	server_value = str(self.server.getObj()) if hasattr(self.server, 'getObj') else str(self.server)
	# 	properties.append(Property(name="otupy:webservice:server", value=server_value))
	if self.port is not None:
		properties.append(Property(name="otupy:webservice:port", value=str(self.port)))
	if self.owner is not None:
		properties.append(Property(name="otupy:webservice:owner", value=self.owner))
	
	endpoints = [XsUri(self.endpoint)] if self.endpoint else None
	
	return Service(
		name="web-service",
		bom_ref=generate_bom_ref("webservice"),
		description=self.description,
		endpoints=endpoints,
		properties=properties
	)

WebService.to_cyclonedx = to_cyclonedx
