import re

from otupy import Record
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf

class SId(Record):
	""" Service Identifier

		This is a reference to the service, using the following schema:

		<type>:<subtype>/<domain>/<namespace>/<name>@<version>

		Some fields might not be set; in this case they are not present or equal to `None`.
		
		The service identifier is conceveid to avoid collisions as much as possible; services that
		are visible in two different scopes (e.g., Kubernetes pods and namespace should create
		the same identifier in different places (i.e., Kubernets and linux server.

	"""
	type: str = None
	"""Main type for this service. This is set according to `ServiceType`. """
	subtype: str = None
	""" Subtype for the service. This typically derives from specific settings of the `ServiceType`."""
	domain: str = None
	""" Domain of the service (e.g. OpenStack domain)"""
	namespace: str = None
	""" Tenant/namespace of the service """
	name: str = None
	""" The internal name used by the `ServiceType` to identify the resource. """
	version: str = None
	""" Used to identify specific versions (this is mostly used for software """

	def __init__(self, sid:dict = None, type:str = None, subtype:str = None,
			domain: str = None, namespace:str = None, name: str = None, version:str=None):
		""" Initialize a Sid

			The init function is specifically conceived to support the otupy serialization mechanism.
			Other helpers are provided to automatically instantiate the fields for a `Sid`.
		"""
		if sid is not None:
			self.type=sid.type
			self.subtype=sid.subtype
			self.domain=sid.domain
			self.namespace=sid.namespace
			self.name=sid.name
			self.version=sid.version
		else:
			self.type=type
			self.subtype=subtype
			self.domain=domain
			self.namespace=namespace
			self.name=name
			self.version=version


	@staticmethod
	def create_from_service_type(service_type:object, domain=None, namespace=None):
		""" Create a SId from a service type object

			Create a SId by taking the type from the name used to register a `ServiceType`, and the subtype from 
			a method that should be exposed by the object, if available. It uses the same name of the `service_type`
			and tries to get a version from it. `domain` and `namespace` are expected as
			input.

			@:param service_type: Any object that is registered as a `ServiceType`. We expect the class
				itself to be provided, but we also manage a `ServiceType`.
			@:param domain: Anything can be used to represent a domain internal to the scope.
			@:param namespace: Anyting that is used to separate names or resources within the domain.
			@:return: A SId object built in a standard way.
		"""
		if isinstance(service_type, ServiceType):
			service_type = service_type.getObj()

		stype = ServiceType.get_type_name(type(service_type))
		try:
			subtype = service_type.get_subtype()
		except:
			subtype = None
		name = service_type.name
		try:
			version = service_type.version
		except:
			version = None
		
		return SId(type=stype, subtype=subtype, domain=domain, namespace=namespace, name=name, version=version)
	
	@staticmethod
	def from_str(sid: str):
		""" Create a SId from its string representation

			@:param sid: A string following the SId format
			@:return: A SId class
		"""
		sid_list=re.split(':|/|@', sid)
		return SId(type=sid_list[0] if sid_list[0] != 'None' else None, 
							subtype=sid_list[1] if sid_list[1] != 'None' else None, 
							domain=sid_list[2] if sid_list[2] != 'None' else None, 
							namespace=sid_list[3] if sid_list[3] != 'None' else None,
						  	name=sid_list[4] if sid_list[4] != 'None' else None, 
							version=sid_list[5] if sid_list[5] != 'None' else None)

	def __eq__(self, other):
		""" Compare two sids for equality """
		return  self.name == other.name and \
							self.type == other.type and \
							self.subtype == other.subtype and \
							self.domain == other.domain and \
							self.namespace == other.namespace and \
							self.version == other.version

	def __str__(self):
		""" Return the SId as simple string according to the initial scheme """
		return f"{str(self.type)}:{str(self.subtype)}/{str(self.domain)}/{str(self.namespace)}/{str(self.name)}@{str(self.version)}"


class Service(Record):
	""" Service components

		The `Service` is any digital resource present in a system, including software, APIs, devices, infrastructures 
		and their elementary components. `Service`s have dependencies between them (aka `Link`s), which 
		describe how they are related and how vulnerabilities might propagate.

		A `Service` may also be an composition of more elementary subservices. In this case, both the `Service` and
		its sub`Service`s are described and linked, which allows to expose the system composition and topology
		with different level of granularity according to the trust level.

		The `domain` and `namespace` field are kept for backward compatibility, but may be removed
		in future versions because they are already included in the `SId`. Do not rely or use these
		fields.

	"""

	name: Name = None
	""" Name of the service """
	sid: SId = None
	""" Id of the service, to be create as unique as possible """
	domain: str = None
	""" Domain of the service (e.g. OpenStack domain)"""
	namespace: str = None
	""" Tenant/namespace of the service """
	type: ServiceType = None
	"""It identifies the type of the service"""
	subservices: ArrayOf(SId) = None 
	""" Subservices of the main service """
	owner: str = None
	""" owner of the service """
	release: str = None
	""" Release version of the service """

	def __init__(self, service:object = None, name:Name = None, domain:str = None, namespace:str = None, sid:SId= None,
						type:ServiceType = None, subservices:ArrayOf(str) = None, owner:str = None, release:str = None): # type: ignore
		if isinstance(service, Service):
			self._init_from_service(service=service)
		else:
			self._init_from_params(name=name, domain=domain, namespace=namespace, sid=sid,
						type=type, subservices=subservices, owner=owner, release=release)
			
	def _init_from_service(self, service):
		self.name = service.name 
		self.sid = service.sid
		self.domain = service.domain 
		self.namespace = service.namespace 
		self.type = service.type 
		self.subservices = service.subservices 
		self.owner = service.owner 
		self.release = service.release 

	def _init_from_params(self, name:Name = None, domain:str = None, namespace:str = None, sid:SId = None, type:ServiceType = None, 
				subservices:ArrayOf(str) = None, owner:str = None, release:str = None): # type: ignore
		self.name = name
		self.sid = sid
		self.domain = domain
		self.namespace = namespace
		self.type = ServiceType(type)
		self.subservices = subservices
		self.owner = owner
		self.release = release

	def __repr__(self):
		return (f"Service(name={self.name.getObj()}, id={self.sid}, type={self.type}, "
	             f"subservices={self.subservices}, owner={self.owner}, release={self.release}) ")
	
	def __str__(self):
		return self.__repr__()

