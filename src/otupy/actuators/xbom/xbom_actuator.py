""" Skeleton `Actuator` for XBOM profile

	This module implements an `Actuator` for the XBOM profile.
	It manages common operations (like answering the `query` command and the interface to implement 
	specific sofware for different environments. It should be used alone, because it does not return
	`Xbom` data until the concrete implementation of the discovery methods is provided.

	Concrete implementation of this interface should implement the following methods:
	- discover_services(): Must fill in the internal `services` member with `Service` instances.
	- discover_links(): Must fill in the internal `links` member with `Link` instances.
	This will be subject to changes till the XBOM profile is stable.
"""

import logging

from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature
import otupy.profiles.xbom as xbom

from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.consumer import Consumer
from otupy.profiles.xbom.data.service import Service
from otupy.profiles.xbom.data.link import Link
from otupy.profiles.xbom.data.xbom import CyclonedxXbom
from otupy.profiles.xbom.data.abstract_xbom import Xbom
from otupy.profiles.xbom.data.sbom_format import SbomFormat

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)
""" Supported OpenC2 Version """

# An implementation of the ctxd profile. 
# Registry of BOM implementations by format
_BOM_REGISTRY: dict[SbomFormat, type[Xbom]] = {
	SbomFormat.cyclonedx: CyclonedxXbom,
}


class XBOMActuator:
	""" XBOM Actuator base class

		This class provides the common implementation of the XBOM `Actuator`.
	"""

	boms: ArrayOf(Xbom) = None # type: ignore
	""" List of discovered BOMs """
	
	sbom_format: SbomFormat = SbomFormat.cyclonedx
	""" The SBOM format to use for creating BOMs (set from target) """
	
	def __init__(self, **kwargs):
		""" Initialization

			Common parameters expected for all actuators:

			- auth: Authentication information to connect to external APIs for discovering services and links
			- config: Additional configuration parameters specific for each actuator (ofter related to endpoints or parameters of the external APIs)
			- peers: A list of `Consumer`s that host the definition of external services (usually found as peers in links). They are currently provided
				at initialization time, waiting for some more automated discovery mechanism.
			- owner: The owner of the resource (in case of cloud resources, effective owners should be discovered by the actuator)
			- specifiers: This is the description of the actuator (e.g., its identifiers).

		"""
		self.auth = kwargs['auth'] if 'auth' in kwargs else None
		self.config = kwargs['config'] if 'config' in kwargs else None
		self.peers = kwargs['peers'] if 'peers' in kwargs else None
		self.owner = kwargs['owner'] if 'owner' in kwargs else None
		self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None
		self.sbom_format = SbomFormat.cyclonedx
		self.boms = ArrayOf(Xbom)()
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()

	def create_bom(self) -> Xbom:
		""" Factory method to create a BOM instance based on the current sbom_format
		
			This method should be used by actuators instead of directly instantiating Xbom().
			It creates the appropriate BOM type based on the format requested in the target.
		
			:return: A new BOM instance of the appropriate type
			:raises NotImplementedError: If the requested format is not supported
		"""
		bom_class = _BOM_REGISTRY.get(self.sbom_format)
		if bom_class is None:
			raise NotImplementedError(f"SBOM format {self.sbom_format} is not supported")
		return bom_class()

	def get_bom_by_name(self, name: str) -> Xbom | None:
		""" Find a BOM by the name of its main component or service
		
			:param name: The name of the component or service to find
			:return: The Xbom containing the component/service, or None if not found
		"""
		for bom in self.boms:
			if bom.bom is None:
				continue
			# Check services
			for service in bom.bom.services:
				if service.name == name:
					return bom
			# Check components
			for component in bom.bom.components:
				if component.name == name:
					return bom
		return None

	def get_bom_by_type(self, item_type: type) -> list[Xbom]:
		""" Find all BOMs containing components/services of a specific type
		
			This looks at the otupy:type property to determine the type.
		
			:param item_type: The type class (e.g., Pod, Container, VM)
			:return: List of Xbom objects containing items of the specified type
		"""
		type_name = item_type.__name__.lower()
		matching_boms = []
		
		for bom in self.boms:
			if bom.bom is None:
				continue
			# Check services
			for service in bom.bom.services:
				if service.properties:
					for prop in service.properties:
						if prop.name == "otupy:type" and prop.value == type_name:
							matching_boms.append(bom)
							break
			# Check components
			for component in bom.bom.components:
				if component.properties:
					for prop in component.properties:
						if prop.name == "otupy:type" and prop.value == type_name:
							matching_boms.append(bom)
							break
		return matching_boms

	def add_dependency_between_boms(self, from_bom: Xbom, to_bom: Xbom, comment: str | None = None) -> None:
		""" Add a dependency relationship between two BOMs
		
			This creates an external reference and dependency from one BOM to another.
		
			:param from_bom: The BOM that depends on another
			:param to_bom: The BOM that is depended upon
			:param comment: Optional comment describing the dependency
		"""
		try:
			from_bom.add_dependency_with_external_ref(to_bom, comment=comment)
		except Exception as e:
			logger.warning(f"Failed to add dependency from {from_bom} to {to_bom}: {e}")

	def _build_boms(self) -> None:
		""" Convert all services and links to BOMs

			This method:
			1. Creates a BOM for each service based on its type
			2. Establishes dependency relationships between BOMs from the subservice structure
			3. Adds links to the appropriate BOMs by matching link names to services/components

			This centralizes all BOM creation so that concrete actuators only need
			to populate self.services and self.links.
		"""
		# Create a BOM for each service
		for service in self.services:
			if service.type is None:
				logger.warning("Service %s has no type, skipping BOM creation", service.name)
				continue
			bom = self.create_bom()
			bom.add(service.type.getObj())
			self.boms.append(bom)

		# Create dependency relationships based on subservices
		for service in self.services:
			if service.subservices is not None and len(service.subservices) > 0:
				parent_bom = self.get_bom_by_name(str(service.name))
				if parent_bom is None:
					logger.warning("Could not find parent BOM for service %s", service.name)
					continue
				for child_name in service.subservices:
					child_bom = self.get_bom_by_name(str(child_name))
					if child_bom is not None:
						self.add_dependency_between_boms(
							child_bom, parent_bom,
							comment=f"{child_name} is a subservice of {service.name}"
						)

		# Add links to the appropriate BOMs
		for link in self.links:
			self._add_link_to_bom(link)

	def _add_link_to_bom(self, link: Link) -> None:
		""" Add a link to the appropriate BOM based on the services/components involved in the link

			Searches through existing BOMs to find one whose service or component name matches
			the link name, then adds the link to that BOM.

			:param link: The Link object to add.
		"""
		for bom in self.boms:
			if bom.bom is None:
				continue
			if len(bom.bom.services) > 0:
				for service in bom.bom.services:
					if service.name == link.name.getObj():
						bom.add(link)
						return
			if len(bom.bom.components) > 0:
				for component in bom.bom.components:
					if component.name == link.name.getObj():
						bom.add(link)
						return
		logger.warning("Could not find BOM to add link %s", link.name)


	def run(self, cmd):
		""" Entry point for running commands

			This is the actuator entry point to receive OpenC2 commands from the otupy `Consumer`.

			:param cmd: A `Command` in the format of the otupy framework.
			:return: `Response` to the provided command.
		"""
		if not xbom.validate_command(cmd):
			return Response(status=StatusCode.NOTIMPLEMENTED, status_text='Invalid Action/Target pair')
		if not xbom.validate_args(cmd):
			return Response(status=StatusCode.NOTIMPLEMENTED, status_text='Option not supported')

		# Check if the Specifiers are actually served by this Actuator
		try:
			if not self.__is_addressed_to_actuator(cmd.actuator.getObj()):
				return Response(status=StatusCode.NOTFOUND, status_text='Requested Actuator not available')
		except AttributeError:
			# If no actuator is given, execute the command
			pass
		except Exception as e:
			return Response(status=StatusCode.INTERNALERROR, status_text='Unable to identify actuator')

#		try:
		match cmd.action:
			case Actions.query:
				response = self.query(cmd)
			case _:
				response = self.__notimplemented(cmd)
#		except Exception as e:
#			return self.__servererror(cmd, e)

		return response

	def __is_addressed_to_actuator(self, actuator):
		""" Checks if this Actuator must run the command """
		if actuator is None or len(actuator) == 0:
			# Empty specifier: run the command
			return True

		for k,v in actuator.items():		
			try:
				# For now, just check if the asset_id matches
				if(v == self.specifiers['asset_id']):
					return True
			except KeyError:
				pass

		return False

	def query(self, cmd):
		""" Query action

			This method implements the `query` action.

			:param cmd: The `Command` including `Target` and optional `Args`.
			:return: A `Response` including the result of the query and appropriate status code and messages.
		"""
		if ( type(cmd.target.getObj()) == Features): 
			r = self._query_feature(cmd)
		elif (isinstance(cmd.target.getObj(), xbom.SbomCtx)):
			# SBOM target with format and names fields
			r = self._query_sbom(cmd)
		else:
			return Response(status=StatusCode.BADREQUEST, status_text="Querying " + cmd.target.getName() + " not supported")

		return r

	def _query_feature(self, cmd):
		""" Query features

			Implements the 'query features' command according to the requirements in Sec. 4.1 of the Language Specification.

			:param cmd: The `Command` including `Target` and optional `Args`.
			:return: A `Response` including the result of the query and appropriate status code and messages.
		"""
		features = {}
		for f in cmd.target.getObj():
			match f:
				case Feature.versions:
					features[Feature.versions.name]=ArrayOf(Version)([OPENC2VERS])	
				case Feature.profiles:
					pf = ArrayOf(Nsid)()
					pf.append(Nsid(xbom.Profile.nsid))
					features[Feature.profiles.name]=pf
				case Feature.pairs:
					features[Feature.pairs.name]=xbom.AllowedCommandTarget
				case Feature.rate_limit:
					return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Feature 'rate_limit' not yet implemented")
				case _:
					return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid feature '" + f + "'")

		res = None
		try:
			res = xbom.Results(features)
		except Exception as e:
			return self.__servererror(cmd, e)

		return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)

	def get_services(self, name: Name | None = None, filter: ServiceType | None = None) -> list:
		""" Returns the list of current services in servuceformat

			Returns the list of discovered services. Filter by name and type.

			:param name: The name of the service to retrieve (all if not set).
			:param filter: The type of service (given by a void instance of `ServiceType`).
			:return: A list of services that match the searching criteria.
		"""
		service_list= []
		for s in self.services:
			if filter == None or ( type(s.type.getObj()) == filter ):
				if name == None or ( s.name == name ):
					service_list.append(s)

		return service_list
		
	def get_consumer(self, service_name: Name) -> Consumer:
		""" Returns consumer data

			Returns the `Consumer` data for the selected service name.

			:param service_name: name of the service which consumer is searched.
			:return: The consumer serving the given service, if any, None otherwise.
		"""
		consumer=None
		for p in self.peers:
			if Name(p['service_name']) == service_name:
				consumer = Consumer(**p['consumer'])
				logger.debug("Found consumer %s for %s", consumer, service_name)
				break

		return consumer

	def _query_sbom(self, cmd):
		""" Query SBOM with specific format and names filter

			Handles the SbomCtx target which allows specifying both the SBOM format
			and a list of component/service names to filter by.

			:param cmd: The `Command` including `Target` and optional `Args`.
			:return: A `Response` including filtered BOMs.
		"""
		sbom_target = cmd.target.getObj()
		res = {}

		if not (cmd.args.get('cached') == True):
			self._update()

		# Get format if specified and set it for BOM creation
		if sbom_target.get('format') is not None:
			self.sbom_format = sbom_target.get('format')

		# Get names filter if specified
		names_filter = sbom_target.get('names')
		
		# Filter BOMs by names if specified
		filtered_boms = self.boms
		if names_filter is not None and len(names_filter) > 0:
			filtered_boms = ArrayOf(Xbom)()
			for bom in self.boms:
				if bom.bom is None:
					continue
				# Check if any component or service in this BOM matches the filter names
				for name_filter in names_filter:
					# Check services
					if hasattr(bom.bom, 'services') and bom.bom.services:
						for service in bom.bom.services:
							if str(service.name) == name_filter:
								filtered_boms.append(bom)
								break
					# Check components
					if hasattr(bom.bom, 'components') and bom.bom.components:
						for component in bom.bom.components:
							if component.name == name_filter:
								filtered_boms.append(bom)
								break
					if bom in filtered_boms:
						break

		# Return results based on name_only argument
		if cmd.args.get('name_only') == True:
			res['bom_names'] = ArrayOf(Name)()
			# Collect all service/component names from filtered BOMs
			for b in filtered_boms:
				if b.bom:
					if hasattr(b.bom, 'services') and b.bom.services:
						for service in b.bom.services:
							res['bom_names'].append(Name(service.name))
					if hasattr(b.bom, 'components') and b.bom.components:
						for component in b.bom.components:
							res['bom_names'].append(Name(component.name))
		else:
			res['boms'] = filtered_boms
			# Also include names for convenience
			res['bom_names'] = ArrayOf(Name)()
			for b in filtered_boms:
				if b.bom:
					if hasattr(b.bom, 'services') and b.bom.services:
						for service in b.bom.services:
							res['bom_names'].append(Name(service.name))
					if hasattr(b.bom, 'components') and b.bom.components:
						for component in b.bom.components:
							res['bom_names'].append(Name(component.name))

		if len(res) > 0:
			logger.debug("Returning filtered SBOMs: %s", res)
			return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=xbom.Results(**res))
		else:
			return Response(status=StatusCode.OK, status_text="No matching BOMs found")

	def _update(self):
		""" Update boms

			This method should be run before getting the list of boms.
			Every concrete implementation of actuators must implement the `discover_services()` and `discover_links()` methods.
			Does not return anything, just update the internal members `services` and `links`.

			:return: None
		"""
		self.boms = ArrayOf(Xbom)()
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()
		self.discover_services()
		self.discover_links()
		self._build_boms()
		
	def __notimplemented(self, cmd):
		""" Default response

			Default response returned in case an `Action` is not implemented.
			The `cmd` argument is only present for uniformity with the other handlers.

			:param cmd: The `Command` that triggered the error.
			:return: A `Response` with the appropriate error code.

		"""
		return Response(status=StatusCode.NOTIMPLEMENTED, status_text='Command not implemented')

	def __servererror(self, cmd, e):
		""" Internal server error

			Default response in case something goes wrong while processing the command.

			:param cmd: The command that triggered the error.
			:param e: The Exception returned.
			:return: A standard INTERNALSERVERERROR response.
		"""
		logger.warn("Returning details of internal exception")
		logger.warn("This is only meant for debugging: change the log level for production environments")
		if(logging.root.level < logging.INFO):
			return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error: ' + str(e))
		else:
			return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')
