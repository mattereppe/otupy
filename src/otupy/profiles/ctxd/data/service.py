import dataclasses

import otupy.types.base
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.link import Link
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf

class Service(otupy.types.base.Record):

    #Class Service is implemented
	
	name: Name = None
	""" Name of the service """
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

	def __init__(self, name:Name = None, type:ServiceType = None, #links:ArrayOf(Name) = None, # type: ignore
					    subservices:ArrayOf(Name) = None, owner:str = None, release:str = None): # type: ignore
		if isinstance(name, Service):
			self._init_from_service(name)
		else:
			self._init_from_params(name, type, subservices, owner, release)
#self._init_from_params(name, type, links, subservices, owner, release)
		self.validate_fields()
			
	def _init_from_service(self, service):
		self.name = service.name if service.name is not None else None
		self.type = service.type if service.type is not None else None
#		self.links = service.links if service.links is not None else None
		self.subservices = service.subservices if service.subservices is not None else None
		self.owner = service.owner if service.owner is not None else None
		self.release = service.release if service.release is not None else None

	def _init_from_params(self, name:Name = None, type:ServiceType = None, # links:ArrayOf(Name) = None, # type: ignore
					    subservices:ArrayOf(Name) = None, owner:str = None, release:str = None): # type: ignore
		self.name = name
		self.type = type
#self.links = links
		self.subservices = subservices
		self.owner = owner
		self.release = release

#	def add_link(self, link: Link):
#self.links.append(link)

	def __repr__(self):
		return (f"Service(name={self.name}, type={self.type}, "
#f"links={self.links}, subservices={self.subservices}, owner={self.owner}, ")
	             f"subservices={self.subservices}, owner={self.owner}, ")
	
	def __str__(self):
		return f"Service(" \
	            f"name={self.name.getObj()}, " \
	            f"type={self.type}, " \
               f"subservices={self.subservices}, " \
					f"owner={self.owner}, " \
					f"release={self.release}, " 

	def validate_fields(self):
		if self.name is not None and not isinstance(self.name, Name):
			raise TypeError(f"Expected 'name' to be of type {Name}, but got {type(self.name)}")
		if self.type is not None and not isinstance(self.type, ServiceType):
			raise TypeError(f"Expected 'type' to be of type {ServiceType}, but got {type(self.type)}")
#if self.links is not None and not isinstance(self.links, Array):
#raise TypeError(f"Expected 'links' to be of type {Array}, but got {type(self.links)}")
		if self.subservices is not None and not isinstance(self.subservices, Array):
			raise TypeError(f"Expected 'subservices' to be of type {Array}, but got {type(self.subservices)}")
		if self.owner is not None and not isinstance(self.owner, str):
			raise TypeError(f"Expected 'owner' to be of type str, but got {type(self.owner)}")
		if self.release is not None and not isinstance(self.release, str):
			raise TypeError(f"Expected 'release' to be of type str, but got {type(self.release)}")
