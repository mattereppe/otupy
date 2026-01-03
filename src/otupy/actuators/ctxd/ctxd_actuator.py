""" Skeleton `Actuator` for CTXD profile

	This module implements an `Actuator` for the CTXD profile.
	It manages common operations (like answering the `query` command and the interface to implement 
	specific sofware for different environments. It should be used alone, because it does not return
	`Services` or `Links`.

	Concrete implementation of this interface should implement the following methods:
	- discover_services(): Must fill in the internal `services` member with `Service` instances.
	- discover_links(): Must fill in the internal `links` member with `Link` instances.
"""

import logging
import sys


from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature
import otupy.profiles.ctxd as ctxd

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.consumer import Consumer

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)
""" Supported OpenC2 Version """

# An implementation of the ctxd profile. 
class CTXDActuator:
	""" Context Discovery actuator for the ctxd profile.

		This class provides the base implementation of the CTXD `Actuator`.
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
		self.auth = kwargs['auth'] if 'auth' in kwargs else None
		self.config = kwargs['config'] if 'config' in kwargs else None
		self.peers = kwargs['peers'] if 'peers' in kwargs else None
		self.owner = kwargs['owner'] if 'owner' in kwargs else None
		self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()


	def run(self, cmd):
		""" Entry point for running commands

			This is the actuator entry point to receive OpenC2 commands from the otupy `Consumer`.

			:param cmd: A `Command` in the format of the otupy framework.
			:return: `Response` to the provided command.
		"""
		if not ctxd.validate_command(cmd):
			return Response(status=StatusCode.NOTIMPLEMENTED, status_text='Invalid Action/Target pair')
		if not ctxd.validate_args(cmd):
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
		elif (type(cmd.target.getObj()) == ctxd.Context): #Discovery Context can accept also "context" as a target
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
					pf.append(Nsid(ctxd.Profile.nsid))
					features[Feature.profiles.name]=pf
				case Feature.pairs:
					features[Feature.pairs.name]=ctxd.AllowedCommandTarget
				case Feature.rate_limit:
					return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Feature 'rate_limit' not yet implemented")
				case _:
					return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid feature '" + f + "'")

		res = None
		try:
			res = ctxd.Results(features)
		except Exception as e:
			return self.__servererror(cmd, e)

		return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)

	def get_services(self, name: Name = None, filter: ServiceType = None) -> [] :
		""" Returns the list of current services

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


	def _query_context(self, cmd):
		""" Returns the current context (services and links)

			Updates the list of services/links (if necessary) and returns them. The main task is to build the expected response
			(names only or full description), while the concrete discovery is managed by the `_udpdate()` method.
		"""
		services = cmd.target.obj.services
		links = cmd.target.obj.links
		res = {}

		if not (cmd.args.get('cached') == True):
			self._update()

		if(services is not None):
			if(cmd.args.get('name_only') == True):
				res['service_names'] = ArrayOf(Name)()
			else:
				res['services'] = ArrayOf(Service)()
			if self.services is not None:
				for i in self.services:
					if (len(services) == 0) or i.name in services:
						if(cmd.args.get('name_only') == True):
							res['service_names'].append(i.name)
						else:
							res['services'].append(i)
		if(links is not None):
			if(cmd.args.get('name_only') == True):
				res['link_names'] = ArrayOf(Name)()
			else:
				res['links'] = ArrayOf(Link)()
			if self.links is not None:
				for i in self.links:
					if(len(links) == 0) or i.name in links:
						if(cmd.args.get('name_only') == True):
							res['link_names'].append(i.name)
						else:
							res['links'].append(i)

		if len(res) > 0:
			return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(**res))
		else:
			return Response(status=StatusCode.OK, status_text="Command received: heartbeat")
			
	def _update(self):
		""" Update services and links

			This method should be run before getting links and services
			Every concrete implementation of actuators must implement the `discover_services()` and `discover_links()` methods.
			Does not return anything, just update the internal members `services` and `links`.

			:return: None
		"""
		self.services = ArrayOf(Service)()
		self.discover_services()
		self.links = ArrayOf(Link)()
		self.discover_links()
		
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
