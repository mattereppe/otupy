from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy.types.base import Record, ArrayOf
from otupy.profiles.xbom.data.endpoint import Endpoint
from cyclonedx.model import Property, XsUri
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class API(XBOMObject):
	
	""" Application Programming Interface

		The abstraction of any API that can be invoked by the network (TODO: extend to other kind of local APIs). 
		The purpose is to include both
		older-style RPCs and newer WSDL, REST, SOAP, etc, as well as any custom interface and API. 
		
		Given the very broad scope and heterogeneous terminology used by different architectures and protocols,
		this preliminary definition will likely be extended and refined in the future to better include the different
		alternatives.
	"""
	type: str = None
	""" Type of API (refer to RFC or other standard definition)  """
	endpoints: ArrayOf(Endpoint) = None
	""" A list of endpoints that are exposed by this service """
	provider: str = None
	""" Provider of the API """
	version: str = None
	""" API version """

	def __init__(self, api = None, description = None, type = None, name = None, endpoints = None, id = None, provider = None, version=None):
		if isinstance(api, API):
			super().__init__(name=api.name, description=api.description, id=api.id)
			self.type=api.type
			self.endpoints=api.endpoints
			self.provider=api.provider
			self.version=api.version
		else:
			super().__init__(name=name, description=description, id=id)
			self.type = type 
			self.endpoints = endpoints 
			self.provider = provider 
			self.version = version

	def getId(self, domain=None, namespace=None):
		return "api:" + "/" + str(domain) + "/" + str(namespace) + "/" + str(self.name) + "@" + str(self.version)
		
	def __repr__(self):
		return (f"API({super().__repr__()},  type={self.type}, "
	             f"endpoints={self.provider},provider={self.provider},version={self.version})")
	
	def __str__(self):
		return self.__repr__()
	
	def as_cyclonedx(self) -> Service:
		"""Convert API to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		import re
		
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
				endpoint_props = endpoint.as_cyclonedx(prefix=f"otupy:api:endpoint:{i}")
				properties.extend(endpoint_props)
		
		return Service(
			name=self.name if self.name is not None else None,
			bom_ref=self.getId() if self.id is not None else generate_bom_ref(self),
			description=self.description,
			endpoints=endpoint_uris if endpoint_uris else None,
			properties=properties
		)
