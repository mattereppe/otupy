import logging

import otupy.types.base
import otupy.transfers
import otupy.encoders
from otupy import Transfer, Transfers, Encoder, Encoders, Map, Extensions
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol
from otupy.profiles.ctxd.profile import nsid

logger = logging.getLogger(__name__)

class Consumer(otupy.types.base.Record):
	"""Consumer

		This class contains all mandatory and optional data to connect to an OpenC2 Consumer.
		Although a typical OpenC2 communication stack will likely use JSON/HTTPS, there
		are not default settings for this class.
	"""
	host: str = None
	""" Hostname or IP address """
	port: int = None
	""" port used to connect to the actuator """
	protocol: L4Protocol = None
	""" protocol used to connect to the actuator """
	endpoint: str = None
	""" path to the endpoint (.../.well-known/openc2) """
	transfer: str = None
	""" transfer protocol used to connect to the actuator """
	encoding: str = None
	""" encoding format used to connect to the actuator """	
	profile: str = None
	""" profile implemented by this Consumer. Default to the context discovery profile. """
	actuator: dict = None
	""" actuator specifiers """

	def __init__(self, host:str = None, port:int = None, protocol:int = None, endpoint:str = None, 
			transfer:str = None, encoding:str = None,
			profile:str = nsid, actuator = None):
		self.host = Hostname(host) if host is not None else None
		self.port = port if port is not None else None
		self.protocol = L4Protocol[protocol] if protocol is not None else None
		self.endpoint = endpoint if endpoint is not None else None
		self.transfer = Transfers[transfer] if transfer is not None else None
		self.encoding = Encoders[encoding].value if encoding is not None else None
		self.profile = profile # Default value assigned in function declaration
#self.actuator = actuator if actuator is not None else None
		specifiers = None
		if actuator is not None:
			try:
				specifiers = Extensions['Actuators'][profile](actuator)
			except:
				logger.error("Cannot instantiate %s profile for consumer: %s", profile, consumer)
		self.actuator=specifiers

		self.validate_fields()

	def __repr__(self):
		return (f"Consumer(host={self.host}, port={self.port}, protocol='{self.protocol}'"
	             f"endpoint={self.endpoint}, transfer={self.transfer}, encoding='{self.encoding}')"
					 f"profile={self.profile}, actuator={self.actuator}")
	
	def __str__(self):
		return f"Consumer(" \
	            f"host={self.host}, " \
	            f"port={self.port}, " \
	            f"protocol={self.protocol}, " \
	            f"endpoint={self.endpoint}, " \
					f"transfer={self.transfer}, " \
	            f"encoding={self.encoding}), " \
					f"profile={self.profile}, " \
					f"actuator={self.actuator}"

	def validate_fields(self):
		if self.host is not None and not isinstance(self.host, Hostname):
			raise TypeError(f"Expected 'host' to be of type {Hostname}, but got {type(self.host)}")
		if self.port is not None and not isinstance(self.port, int):
			raise TypeError(f"Expected 'port' to be of type {int}, but got {type(self.port)}")		
		if self.protocol is not None and not isinstance(self.protocol, L4Protocol):
			raise TypeError(f"Expected 'protocol' to be of type {L4Protocol}, but got {type(self.protocol)}")
		if self.endpoint is not None and not isinstance(self.endpoint, str):
			raise TypeError(f"Expected 'endpoint' to be of type {str}, but got {type(self.endpoint)}")
		if self.transfer is not None and not issubclass(self.transfer, Transfer):
			raise TypeError(f"Expected 'transfer' to be of type {Transfer}, but got {type(self.transfer)}")
		if self.encoding is not None and not issubclass(self.encoding, Encoder):
			raise TypeError(f"Expected 'encoding' to be of type {Encoding}, but got {type(self.encoding)}")
		if self.actuator is not None and not isinstance(self.actuator, dict):
			raise TypeError(f"Expected 'actuator' to be of type {dict}, but got {type(self.actuator)}")


