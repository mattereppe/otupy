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

	def __init__(self, description = None, type = None, name = None, endpoints = None, id = None, provider = None):
		self.description = description if description is not None else None
		self.type = type if type is not None else None
		self.id = id if id is not None else None
		self.name = name if name is not None else None
		self.endpoints = endpoints if endpoints is not None else None
		self.provider = provider if provider is not None else None

	def __repr__(self):
		return (f"API({super().__repr__()}, type={self.type},\
		  endpoints={self.endpoints}, provider={self.provider})")
	
	def __str__(self):
		return self.__repr__()

	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.type is not None and not isinstance(self.type, str):
			raise TypeError(f"Expected 'type' to be of type str, but got {type(self.type)}")
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type str, but got {type(self.name)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.endpoints is not None and not isinstance(self.endpoints, ArrayOf(Endpoint)):
			raise TypeError(f"Expected 'endpoints' to be of type ArrayOf(Endpoint), but got {type(self.endpoints)}")
		if self.provider is not None and not isinstance(self.provider, str):
			raise TypeError(f"Expected 'provider' to be of type {str}, but got {type(self.provider)}")

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
						# If URI validation still fails, skip it
						# The original URI will still be preserved in endpoint properties
						pass
				# Add endpoint properties
				endpoint_props = endpoint.as_cyclonedx(prefix=f"otupy:api:endpoint:{i}")
				properties.extend(endpoint_props)
		
		return Service(
			name=self.name if self.name is not None else None,
			bom_ref=generate_bom_ref("api"),
			description=self.description,
			endpoints=endpoint_uris if endpoint_uris else None,
			properties=properties
		)
