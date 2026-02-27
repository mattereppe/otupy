import dataclasses

import otupy.types.base
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.link import Link
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf

class Service(otupy.types.base.Record):
	""" Service components

		The `Service` is any digital resource present in a system, including software, APIs, devices, infrastructures 
		and their elementary components. `Service`s have dependencies between them (aka `Link`s), which 
		describe how they are related and how vulnerabilities might propagate.

		A `Service` may also be an composition of more elementary subservices. In this case, both the `Service` and
		its sub`Service`s are described and linked, which allows to expose the system composition and topology
		with different level of granularity according to the trust level.
	"""

	name: Name = None
	""" Name of the service """
	id: str = None
	""" Id of the service, to be create as unique as possible """
	domain: str = None
	""" Domain of the service (e.g. OpenStack domain)"""
	namespace: str = None
	""" Tenant/namespace of the service """
	type: ServiceType = None
	"""It identifies the type of the service"""
	subservices: ArrayOf(Name) = None 
	""" Subservices of the main service """
	owner: str = None
	""" owner of the service """
	release: str = None
	""" Release version of the service """

	def __init__(self, service:object = None, name:Name = None, domain:str = None, namespace:str = None, id:str= None,
						type:ServiceType = None, subservices:ArrayOf(str) = None, owner:str = None, release:str = None): # type: ignore
		if isinstance(service, Service):
			self._init_from_service(service=service)
		else:
			self._init_from_params(name=name, domain=domain, namespace=namespace, id=id,
						type=type, subservices=subservices, owner=owner, release=release)
			
	def _init_from_service(self, service):
		self.name = service.name 
		self.id = service.id
		self.domain = service.domain 
		self.namespace = service.namespace 
		self.type = service.type 
		self.subservices = service.subservices 
		self.owner = service.owner 
		self.release = service.release 

	def _init_from_params(self, name:Name = None, domain:str = None, namespace:str = None, id:str = None, type:ServiceType = None, 
				subservices:ArrayOf(str) = None, owner:str = None, release:str = None): # type: ignore
		self.name = name
		self.domain = domain
		self.namespace = namespace
		self.type = ServiceType(type)
		self.subservices = subservices
		self.owner = owner
		self.release = release
		self.id = self.type.getObj().getId(domain=domain, namespace=namespace) if id is None else id

	def __repr__(self):
		return (f"Service(name={self.name.getObj()}, id=, type={self.type}, "
	             f"subservices={self.subservices}, owner={self.owner}, release={self.release}) ")
	
	def __str__(self):
		return self.__repr__()

