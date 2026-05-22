""" Skeleton `Actuator` for x-xbom profile

	This module implements an `Actuator` for the x-xbom profile.
	It manages common operations (like answering the `query` command and the interface to implement 
	specific sofware for different environments. It should be used alone, because it does not create
	any xbom. This class and all derived class must discovery bom components using the ctxd data model.

	Concrete implementation of this interface should implement the following methods:
	- discover_context(): Must fill in the internal `services` member with `Service` instances and
  			the internal `links` member with `Link` instances.
"""

import logging
import sys


from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature
from otupy.models.ctxd import Service, SId, Link, Name, ServiceType, LinkType, Consumer
import otupy.profiles.xbom as xbom
import otupy.models.xbom




logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)
""" Supported OpenC2 Version """
DEFAULT_XBOM_FORMAT=xbom.XbomFormat.ctxd
""" Default Xbom format to use if not included in the Command """
DEFAULT_XBOM_ENCODING=xbom.XbomEncoding.json
""" Default Xbom encoding to use if not included in the Command """

# An implementation of the xbom profile. 
class XBOMActuator:
	""" Context Discovery actuator for the x-xbom profile.

		This class provides the base implementation of the xbom `Actuator`.
	"""

	services: ArrayOf(Service) = None # type: ignore
	""" Name of the service """
	links: ArrayOf(Link) = None # type: ignore
	"""It identifies the type of the service"""
	
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
		self.auth = kwargs.get('auth',None)
		self.config = kwargs.get('config', None)
		self.peers = kwargs.get('peers', None)
		self.owner = kwargs.get('owner', None)
		self.specifiers = kwargs.get('specifiers', None)
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()
		self.consumer = kwargs.get('consumer', {})
		self.profile = kwargs.get('profile', xbom.Profile.nsid)


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
		logger.debug("Command validation passed")

		# Check if the Specifiers are actually served by this Actuator
		try:
			if not self.__is_addressed_to_actuator(cmd.actuator.getObj()):
				return Response(status=StatusCode.NOTFOUND, status_text='Requested Actuator not available')
		except AttributeError:
			# If no actuator is given, execute the command
			pass
		except Exception as e:
			return Response(status=StatusCode.INTERNALERROR, status_text='Unable to identify actuator')
		logger.debug("Command is addressed to this actuator")

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
		logger.debug("Serving query request")
		if ( type(cmd.target.getObj()) == Features): 
			r = self._query_feature(cmd)
		elif (isinstance(cmd.target.getObj(), xbom.XbomTarget)):
			# SBOM target with format and names fields
			r = self._query_context(cmd)
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
		""" Returns the list of current services

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

	def get_services_by_sid(self, sid: SId = None):
		""" Returns the list of current services

			Returns the list of discovered services. Filter by sid. None fields are
			treated as wildcards.

			:param sid: The sid of the service to retrieve (all if not set).
			:return: A list of services that match the searching criteria.
		"""
		service_list= []
		for s in self.services:
			if sid.type == None or ( sid.type == s.sid.type ):
				if sid.subtype == None or ( sid.subtype == s.sid.subtype):
					if sid.namespace == None or sid.namespace == s.sid.namespace:
						if sid.domain == None or sid.domain == s.sid.domain:
							if sid.name == None or ( sid.name == s.sid.name ):
								if sid.version == None or (sid.name == s.sid.name):
									service_list.append(s)

		return service_list


	def get_links(self, name: Name = None, filter: LinkType = None) -> []:
		""" Returns the list of current links

			REturns the list of discovered links. Filters by name and type.

			:param name: The anme of the link to retrieve (all if not set).
			:param filter: The type of link (given by `LinkType`).
			:return: A list of links that match the searching criteria.
		"""
		link_list=[]
		for l in self.links:
			if filter == None or ( filter == l.link_type ):
				if name == None or (l.name == name):
					link_list.append(l)

		return link_list
		
	def get_consumer(self, name: Name=None, sid: SId=None) -> Consumer:
		""" Returns consumer data

			Returns the `Consumer` data for the selected service name or identifier.

			:param name: name of the service which consumer is searched.
			:param sid: service identifier of the service which consumer is searched.
			:return: The consumer serving the given service, if any, None otherwise.
		"""
		if self.peers is None:
			return None
		if name is None and sid is None:
			return None
		if isinstance(sid, str):
			sid=SId.from_str(sid)	

		consumer=None
		for p in self.peers:
			service_name = Name(p['service_name']) if 'service_name' in p else None
			if 'service_sid' in p:
				if type(p['service_sid'])==str:
					service_sid = SId.from_str(p['service_sid'])
				else:
					service_sid = SId(**p['service_sid'])
			else:
				service_sid = None
			if service_name is not None and name is not None and service_name == Name(name):
				consumer = Consumer(**p['consumer'])
				logger.debug("Found consumer %s for %s", consumer, service_name)
				break
			if service_sid is not None and sid is not None and service_sid == sid:
				consumer = Consumer(**p['consumer'])
				logger.debug("Found consumer by sid %s for %s", consumer, service_sid)
				break

		return consumer


	def _query_context(self, cmd):
		""" Returns the current context (services and links)

			Updates the list of services/links (if necessary) and returns them. The main task is to build the expected response
			(names only or full description), while the concrete discovery is managed by the `_udpdate()` method.
		"""
		bom = None
		num_services=0
		num_links=0

		logger.debug("Looking for current context")
		try:
			if not (cmd.args.get('cached') == True):
				self._update()
		except Exception as e:
			logger.error("Unable to update context: %s", str(e))
			return Response (status=StatusCode.INTERNALERROR, 
					status_text=StatusCodeDescription[StatusCode.INTERNALERROR], 
					results="")

		for s in self.services:
			logger.debug("Found service: %s", s)
			num_services = num_services+1
		for l in self.links:
			logger.debug("Found link: %s", l)
			num_links = num_links+1
		logger.info("Found %d services, %d links", num_services, num_links)

		# Create the xbom
		format = cmd.args.get('format', DEFAULT_XBOM_FORMAT.name)
		logger.debug("Creating xbom %s", format)
		bom = otupy.models.xbom.Xbom.get(format)()
		logger.debug("Creating xbom with %s", type(bom))
		if not bom:
			logger.error("Unsupported xbom format: %s", format)
			return Response(status=StatusCode.BADREQUEST, status_text=f"Unsupported xbom format: {format}")

		consumer = Consumer(**self.consumer, profile=self.profile, actuator=self.specifiers)
		bom.create(services=self.services, links=self.links, consumer=consumer)

		encoding = cmd.args.get('encoding', DEFAULT_XBOM_ENCODING)
		logger.debug("Encoding xbom as %s", encoding)
		try:
			logger.debug("Serializing xbom as %s", encoding)
			serialized_bom = bom.serialize(encoding)
			return  Response(status=StatusCode.OK, 
								status_text=StatusCodeDescription[StatusCode.OK], 
								results= xbom.Results(format=format, encoding=encoding, boms=[serialized_bom]))
		except Exception as e:
			logger.error("Unable to serialize: %s", e)
			return Response(status=StatusCode.INTERNALERROR, 
								status_text='Unable to serialize bom with '+encoding.name+": "+str(e))
			
			
	def _update(self):
		""" Update services and links

			This method should be run before getting links and services
			Every concrete implementation of actuators must implement the `discover_context()` method.
			Does not return anything, just update the internal members `services` and `links`.

			:return: None
		"""
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()
		# Reset everything at the beginning, because links might be updated during the
		# discovery of services for optimization purposes
		self.discover_context()
		
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

