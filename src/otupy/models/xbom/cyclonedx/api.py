import re

from otupy.models.ctxd.api import API

from cyclonedx.model import Property, XsUri
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert API to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	
	properties = [
		Property(name="otupy:type", value="api")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:api:id", value=self.id))
	if self.type is not None:
		properties.append(Property(name="otupy:api:type", value=self.type))
	if self.provider is not None:
		properties.append(Property(name="otupy:api:provider", value=self.provider))
	
	# Add endpoint URIs
	endpoint_uris = []
	if self.endpoints is not None:
		for i, endpoint in enumerate(self.endpoints):
			if endpoint.uri is not None:
				uri_to_add = endpoint.uri
				# TEMPORARY: Sanitize template variables like %(project_id)s to make valid URIs
				# TODO: Remove this once proper template handling is implemented
				# Convert %(var)s format to {var} format which is valid per RFC 6570
				if re.search(r'%\([^)]+\)s', uri_to_add):
					uri_to_add = re.sub(r'%\(([^)]+)\)s', r'{\1}', uri_to_add)
				
				try:
					endpoint_uris.append(XsUri(uri_to_add))
				except Exception:
					pass
			endpoint_props = endpoint.to_cyclonedx(prefix=f"otupy:api:endpoint:{i}")
			properties.extend(endpoint_props)
	
	return Service(
		name=self.name if self.name is not None else None,
		bom_ref=self.getId() if self.id is not None else generate_bom_ref(self),
		description=self.description,
		endpoints=endpoint_uris if endpoint_uris else None,
		properties=properties
	)

API.to_cyclonedx = to_cyclonedx
