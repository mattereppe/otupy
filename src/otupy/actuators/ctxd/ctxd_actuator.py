""" Skeleton `Actuator` for CTXD profile

	This module provides an example to create an `Actuator` for the CTXD profile.
	It only answers to the request for available features.
"""

import logging
import sys


from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature
import otupy.profiles.ctxd as ctxd

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.consumer import Consumer

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)
""" Supported OpenC2 Version """

# An implementation of the ctxd profile. 
class CTXDActuator:
	""" CTXD implementation

		This class provides an implementation of the CTXD `Actuator`.
	"""

	services: ArrayOf(Service) = None # type: ignore
	""" Name of the service """
	links: ArrayOf(Link) = None # type: ignore
	"""It identifies the type of the service"""
	domain : str = None
	asset_id : str = None
	
	def __init__(self, owner, auth, config, peers=[], **kwargs):
		self.auth = auth
		self.config = config
		self.peers = peers
		self.owner = owner
		self.services = ArrayOf(Service)()
		self.links = ArrayOf(Link)()


	def run(self, cmd):
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

		try:
			match cmd.action:
				case Actions.query:
					response = self.query(cmd)
				case _:
					response = self.__notimplemented(cmd)
		except Exception as e:
			return self.__servererror(cmd, e)

		return response

	def __is_addressed_to_actuator(self, actuator):
		""" Checks if this Actuator must run the command """
		if len(actuator) == 0:
			# Empty specifier: run the command
			return True

		for k,v in actuator.items():		
			try:
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
		# Sec. 4.1 Implementation of the 'query features' command and 'query context'
		if cmd.args is not None:
			if ( len(cmd.args) > 1 ):
				return Response(satus=StatusCode.BADREQUEST, statust_text="Invalid query argument")
			if ( len(cmd.args) == 1 ):
				try:
					if cmd.args.get('response_requested') is not None:
						if not(cmd.args['response_requested'] == ResponseType.complete):
							raise KeyError
					elif cmd.args.get('name_only') is not None: #Query can also accept 'name_only' arg
						if not(isinstance(cmd.args['name_only'],bool)):
							raise KeyError
				except KeyError:
					return Response(status=StatusCode.BADREQUEST, status_text="Invalid query argument")

		if ( cmd.target.getObj().__class__ == Features): 
			r = self.query_feature(cmd)
		elif (cmd.target.getObj().__class__ == ctxd.Context): #Discovery Context can accept also "context" as a target
			r = self.query_context(cmd)
		else:
			return Response(status=StatusCode.BADREQUEST, status_text="Querying " + cmd.target.getName() + " not supported")

		return r

	def query_feature(self, cmd):
		""" Query features

			Implements the 'query features' command according to the requirements in Sec. 4.1 of the Language Specification.
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

	def query_context(self, cmd):
		services = cmd.target.obj.services
		links = cmd.target.obj.links
		res_services = ArrayOf(Name)()
		res_links = ArrayOf(Name)()

		try:
			if(services is not None and self.services is not None):
				if(len(services) == 0):
					if(cmd.args.get('name_only') == True):
						for i in self.services:
							res_services.append(i.name)
					else:
						for i in self.services:
							res_services.append(i)
				else:
					if(cmd.args.get('name_only') == True):
						for i in self.services:
							for j in services:
								if(str(i.name.obj) == str(j.obj) and str(i.name.choice) == str(j.choice)):
									res_services.append(i.name) 
					else:
						for i in self.services:
							for j in services:
								if(str(i.name.obj) == str(j.obj) and str(i.name.choice) == str(j.choice)):
									res_services.append(i) 
			if(links is not None and self.my_links is not None):
				if(len(links) == 0):
					if(cmd.args.get('name_only') == True):
						for i in self.my_links:
							res_links.append(i.name)
					else:
						for i in self.my_links:
							res_links.append(i)
				else:
					if(cmd.args.get('name_only') == True):
						for i in self.my_links:
							for j in links:
								if(str(i.name.obj) == str(j.obj) and str(i.name.choice) == str(j.choice)):
									res_links.append(i.name) 
					else:
						for i in self.my_links:
							for j in links:
								if(str(i.name.obj) == str(j.obj) and str(i.name.choice) == str(j.choice)):
									res_links.append(i)
		except Exception as e:
			return self.__servererror(cmd, e)

		if(cmd.args.get('name_only') == True):
			if(services is not None and links is not None):
				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(service_names = res_services, link_names = res_links))
			elif(services is not None and links is None):
				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(service_names = res_services))
			elif(services is None and links is not None):
				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(link_names = res_links))
			
		if(cmd.args.get('name_only') == False):
			if(services is not None and links is not None):
				Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(services = res_services, links = res_links))

				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(services = res_services, links = res_links))
			elif(services is not None and links is None):
				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(services = res_services))
			elif(services is None and links is not None):
				return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results= ctxd.Results(links = res_links))
			
		return Response(status=StatusCode.OK, status_text="Command received: heartbeat")
		
	def _get_services(self, name = None, filter = None):
		service_list= []
		for s in self.services:
			if filter == None or ( type(s.type.getObj()) == filter ):
				if name == None or ( s.name == name ):
					service_list.append(s)

		return service_list
		
	def _get_consumer(self, service_name):
		consumer=None
		for p in self.peers:
			if Name(p['service_name']) == service_name:
				consumer = Consumer(**p['consumer'])
				logger.debug("Found consumer %s for %s", consumer, service_name)
				break

		return consumer


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
