from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.endpoint import Endpoint

class NetworkService(Record):
	
	""" NetworkService

		The abstraction of any function that can be invoked by the network. The purpose is to include both
		older-style RPCs and newer WSDL, REST, SOAP, etc, as well as any custom interface and API. 
		
		Given the very broad scope and heterogeneous terminology used by different architectures and protocols,
		this preliminary defintion will likely be extended and refined in the future to better include the different
		alternatives.
	"""
	name: str = None
	""" A human-friendly name to identify the service; often it will be something related to the implemented function """
	id: str = None
	""" A unique identifier within the infrastructure to identify the service """
	type: str = None
	""" Type of service """
	description: str = None
	""" Generic description the may indicate the specific usage of location of the service instance """
	endpoints: ArrayOf(Endpoint) = None
	""" A list of endpoints that are exposed by this service """
	owner: str = None
	""" Owner of the web service"""

	def __init__(self, description = None, type = None, name = None, endpoints = None, id = None, owner = None):
		self.description = description if description is not None else None
		self.type = type if description is not None else None
		self.id = id if id is not None else None
		self.name = name if name is not None else None
		self.endpoints = endpoints if endpoints is not None else None
		self.owner = owner if owner is not None else None

	def __repr__(self):
		return (f"NetworkService(description={self.description}, name={self.name}, type={self.type}, id={self.id},"
	             f"endpoints={self.owner},owner={self.owner})")
	
	def __str__(self):
		return f"NetworkService(" \
	            f"description={self.description}, " \
	            f"name={self.name}, " \
	            f"id={self.id}, " \
					f"type={self.type}, " \
					f"endpoints={self.endpoints}, " \
	            f"owner={self.owner})"

	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.type is not None and not isinstance(self.type, str):
			raise TypeError(f"Expected 'type' to be of type str, but got {type(self.type)}")
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type str, but got {type(self.name)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.port is not None and not isinstance(self.port, int):
			raise TypeError(f"Expected 'port' to be of type int, but got {type(self.port)}")
		if self.endpoints is not None and not isinstance(self.endpoints, ArrayOf(Endpoint)):
			raise TypeError(f"Expected 'endpoint' to be of type {str}, but got {type(self.endpoint)}")
		if self.owner is not None and not isinstance(self.owner, str):
			raise TypeError(f"Expected 'owner' to be of type {str}, but got {type(self.owner)}")
