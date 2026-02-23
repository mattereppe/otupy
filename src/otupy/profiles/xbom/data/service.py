import dataclasses

import otupy.types.base
from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.link import Link
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf
from cyclonedx.model import Property
from cyclonedx.model.service import Service as CycloneDXService
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record

class Service(Record):
	"""Service"""
	name: Name = None
	""" Name of the service """
	domain: str = None
	""" Domain of the service (e.g. OpenStack domain)"""
	namespace: str = None
	""" Tenant/namespace of the service """
	type: ServiceType = None
	"""It identifies the type of the service"""
#	links: ArrayOf(Name) = None # type: ignore
#	""" Links associated with the service """
	subservices: ArrayOf(Name) = None # type: ignore
	""" Subservices of the main service """
	owner: str = None
	""" owner of the service """
	release: str = None
	""" Release version of the service """

	def __init__(self, name:Name = None, domain:str = None, namespace:str = None, type:ServiceType = None, 
					    subservices:ArrayOf(Name) = None, owner:str = None, release:str = None): # type: ignore
		if isinstance(name, Service):
			self._init_from_service(name)
		else:
			self._init_from_params(name, domain, namespace, type, subservices, owner, release)
		self.validate_fields()
			
	def _init_from_service(self, service):
		self.name = service.name if service.name is not None else None
		self.domain = service.domain if service.domain is not None else None
		self.namespace = service.namespace if service.namespace is not None else None
		self.type = service.type if service.type is not None else None
		self.subservices = service.subservices if service.subservices is not None else None
		self.owner = service.owner if service.owner is not None else None
		self.release = service.release if service.release is not None else None

	def _init_from_params(self, name:Name = None, domain:str = None, namespace:str = None, 
						type:ServiceType = None, 
					    subservices:ArrayOf(Name) = None, owner:str = None, release:str = None): # type: ignore
		self.name = name
		self.domain = domain
		self.namespace = namespace
		self.type = ServiceType(type)
		self.subservices = subservices
		self.owner = owner
		self.release = release

	def __repr__(self):
		return (f"Service(name={self.domain}/{self.namespace}/{self.name.getObj() if self.name else None}, type={self.type}, "
	             f"subservices={self.subservices}, owner={self.owner}, release={self.release}) ")
	
	def __str__(self):
		return f"Service("\
	            f"name={self.domain}/{self.namespace}/{self.name.getObj() if self.name else None}, " \
	            f"type={self.type}, " \
               f"subservices={self.subservices}, " \
					f"owner={self.owner}, " \
					f"release={self.release}) " 

	def validate_fields(self):
		if self.name is not None and not isinstance(self.name, Name):
			raise TypeError(f"Expected 'name' to be of type {Name}, but got {type(self.name)}")
		if self.domain is not None and not isinstance(self.domain, str):
			raise TypeError(f"Expected 'domain' to be of type str, but got {type(self.domain)}")
		if self.namespace is not None and not isinstance(self.namespace, str):
			raise TypeError(f"Expected 'namespace' to be of type str, but got {type(self.namespace)}")
		if self.type is not None and not isinstance(self.type, ServiceType):
			raise TypeError(f"Expected 'type' to be of type {ServiceType}, but got {type(self.type)}")
		if self.subservices is not None and not isinstance(self.subservices, Array):
			raise TypeError(f"Expected 'subservices' to be of type {Array}, but got {type(self.subservices)}")
		if self.owner is not None and not isinstance(self.owner, str):
			raise TypeError(f"Expected 'owner' to be of type str, but got {type(self.owner)}")
		if self.release is not None and not isinstance(self.release, str):
			raise TypeError(f"Expected 'release' to be of type str, but got {type(self.release)}")

	def as_cyclonedx(self) -> any: # type: ignore
		"""Convert Service to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service, component or anything 
		"""
		if self.type is None:
			raise ValueError(f"Service {self.name.getObj() if self.name else None} has no type, cannot convert to CycloneDX format.")
		wrapped_service = self.type.getObj() if self.type is not None else "unknown"
		cdx_service = wrapped_service.as_cyclonedx() if hasattr(wrapped_service, 'as_cyclonedx') else None
		if cdx_service is None:
			raise ValueError(f"Cannot convert service of type {self.type} to CycloneDX format. Missing 'as_cyclonedx' method.")
		if self.name is not None:
			cdx_service.name = str(self.name.getObj())
		
		properties = list()
		if self.domain is not None:
			properties.append(Property(name="otupy:service:domain", value=self.domain))
		if self.namespace is not None:
			properties.append(Property(name="otupy:service:namespace", value=self.namespace))
		if self.owner is not None:
			properties.append(Property(name="otupy:service:owner", value=self.owner))
		if self.release is not None:
			properties.append(Property(name="otupy:service:release", value=self.release))
		
		if hasattr(cdx_service, 'properties') and cdx_service.properties is not None:
			cdx_service.properties.update(properties)
		
		return cdx_service
