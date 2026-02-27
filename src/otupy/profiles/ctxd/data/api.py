from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy.profiles.ctxd.data.endpoint import Endpoint

class API(CTXDObject):
	
	""" Application Programming Interface

		The abstraction of any API that can be invoked by the network (TODO: extend to other kind of local APIs). 
		The purpose is to include both
		older-style RPCs and newer WSDL, REST, SOAP, etc, as well as any custom interface and API. 
		
		Given the very broad scope and heterogeneous terminology used by different architectures and protocols,
		this preliminary defintion will likely be extended and refined in the future to better include the different
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
		return "api:" + str(self.app_type) + "/" + str(domain) + "/" + str(namespace) + "/" + str(self.name) + "@" + str(self.version)
		
	def __repr__(self):
		return (f"API({super().__repr__()},  type={self.type}, "
	             f"endpoints={self.provider},provider={self.provider},version={self.version})")
	
	def __str__(self):
		return self.__repr__()
