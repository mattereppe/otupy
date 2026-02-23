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
from otupy.profiles.ctxd.data import name
import otupy.profiles.xbom as xbom

from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.consumer import Consumer
from otupy.profiles.xbom.data.service import Service
from otupy.profiles.xbom.data.link import Link
from otupy.profiles.xbom.data.xbom import CyclonedxXbom
from otupy.profiles.xbom.data.abstract_xbom import Xbom
from otupy.profiles.xbom.data.sbom_format import SbomFormat

logger = logging.getLogger()

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

	bom: Xbom | None = None
	""" Discovered BOM for this actuator """
	
	sbom_format: SbomFormat = SbomFormat.cyclonedx
	""" The SBOM format to use for BOM creation (set from target) """
	
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
		self.bom = None
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

	def _build_bom(self) -> None:
		""" Convert all services and links into a single BOM for this actuator

			This method:
			1. Creates a single BOM and adds all discovered services/components to it
			2. Establishes dependency relationships from the subservice structure
			3. Adds link properties to the matching services/components

			This centralizes all BOM creation so that concrete actuators only need
			to populate self.services and self.links.
		"""
		self.bom = self.create_bom()
		# TODO: Create a lookup table for the names

		# Add all services to the single BOM
		for service in self.services:
			if service.type is None:
				logger.warning("Service %s has no type, skipping", service.name)
				continue
			try:
				self.bom.add(service)
			except Exception as e:
				logger.error("Faulty service infos: %s", service)
				logger.error("Error adding service %s to BOM: %s", service.name, e)

		# Create dependency relationships based on subservices
		for service in self.services:
			if service.subservices is not None and len(service.subservices) > 0:
				parent_name = service.name.getObj() if hasattr(service.name, 'getObj') else str(service.name)
				
				for subservice in service.subservices:
					# Skip None values in subservices
					if subservice is None:
						logger.warning("Skipping None value in subservices for service %s", parent_name)
						continue
					
					child_name = None
					for s in self.services:
						if s.name == subservice:
							child_name = s.name.getObj() if hasattr(s.name, 'getObj') else str(s.name)
							break

					if child_name is None:
						logger.warning("Could not find matching service for subservice %s in service %s, skipping dependency", subservice, parent_name)
						continue
					
					logger.debug("Adding dependency from %s to subservice %s", parent_name, child_name)
					parent_ref = self.bom.find_ref_by_name(str(parent_name))
					child_ref = self.bom.find_ref_by_name(str(child_name))
					
					if parent_ref is None:
						logger.warning("Could not find parent '%s' in BOM, skipping dependency", parent_name)
						continue
					if child_ref is None:
						logger.warning("Could not find child '%s' (BOM name: '%s') in BOM, skipping dependency", otupy_name, subservice_str)
						continue
						
					self.bom.add_dependency(parent_ref=parent_ref, child_ref=child_ref)

		# Add links as properties to the matching services/components
		for link in self.links:
			self._add_link_to_bom(link)

	def _add_link_to_bom(self, link: Link) -> None:
		""" Add a link as properties to the matching service/component in the BOM

			:param link: The Link object to add.
		"""
		if self.bom is None or self.bom.bom is None:
			logger.warning("No BOM available to add link %s", link.name)
			return
		for service in self.services:
			if service.name == link.name:
				item_name = service.name.getObj() if hasattr(service.name, 'getObj') else str(service.name)
				logger.debug("Adding link properties to service %s for link %s", item_name, link)
				try:
					self.bom.add_link(item_name, link)
				except Exception as e:
					logger.error("Error adding link properties to service %s: %s", service.name, e)
				return
		logger.warning("Could not find service/component '%s' to add link", link.name)


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

	def get_services(self, name: Name | None = None, filter: ServiceType | None = None,
				  domain: str | None = None, namespace: str | None = None) -> list:
		""" Returns the list of current services in servuceformat

			Returns the list of discovered services. Filter by name, type, domain and namespace.

			:param name: The name of the service to retrieve (all if not set).
			:param filter: The type of service (given by a void instance of `ServiceType`).
			:param domain: The domain of the service (all if not set).
			:param namespace: The tenant/namespace of the service (all if not set).
			:return: A list of services that match the searching criteria.
		"""
		service_list= []
		for s in self.services:
			if filter == None or ( type(s.type.getObj()) == filter ):
				if name == None or ( s.name == name ):
					if domain == None or ( getattr(s, 'domain', None) == domain ):
						if namespace == None or ( getattr(s, 'namespace', None) == namespace ):
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
		""" Query SBOM - returns the single BOM for this actuator

			Handles the SbomCtx target which allows specifying the SBOM format
			and a list of component/service names to filter the returned names.

			:param cmd: The `Command` including `Target` and optional `Args`.
			:return: A `Response` including the actuator's BOM.
		"""
		sbom_target = cmd.target.getObj()
		res = {}

		# Get format if specified and set it for BOM creation
		if sbom_target.get('format') is not None:
			self.sbom_format = sbom_target.get('format')

		if not (cmd.args.get('cached') == True):
			self._update()

		if self.bom is None:
			return Response(status=StatusCode.OK, status_text="No BOM available")

		# Get names filter if specified (used to filter bom_names, not the BOM itself)
		names_filter = sbom_target.get('names')

		if cmd.args.get('name_only') == True:
			res['bom_names'] = self._collect_names(names_filter)
		else:
			res['bom'] = self.bom
			res['bom_names'] = self._collect_names(names_filter)

		if len(res) > 0:
			# logger.debug("Returning SBOM: %s", res)
			return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=xbom.Results(**res))
		else:
			return Response(status=StatusCode.OK, status_text="No matching BOMs found")

	def _collect_names(self, names_filter=None):
		""" Collect service/component names from discovered services, optionally filtered

			:param names_filter: A list of name strings to filter by, or None for all names.
			:return: An ArrayOf(Name) with the matching names.
		"""
		names = ArrayOf(Name)()
		for s in self.services:
			if names_filter is None or str(s.name) in names_filter:
				names.append(s.name)
		return names

	def _update(self):
		""" Update boms

			This method should be run before getting the list of boms.
			Every concrete implementation of actuators must implement the `discover_services()` and `discover_links()` methods.
			Does not return anything, just update the internal members `services` and `links`.

			:return: None
		"""
		self.bom = None
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()
		self.discover_services()
		self.discover_links()
		self._build_bom()
		
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
