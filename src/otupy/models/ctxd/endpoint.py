from otupy import Record

class Endpoint(Record):
	
	""" Endpoint

   	Describes a network interface used to access remote functions. Its definition tries to capture all the
	  different elements that are necessary to identify the communication facets of very different network
  		service architectures (e.g., REST, SOAP).	  

		Note: since most of these fields are descriptive and intented to be used by external software, no
		specific data types are created from them.
	"""
	description: str = None
	""" This is a human-friendly description to understand the purpose and location of the service """
	endpoint_type: str = None
	""" The architecture or standard followed by this endpoint definition (e.g., REST, SOAP, WSDL) """
	transport: str = None
	""" Transport protocol used to access the endpoint (may be None if a default/mandatory choice is implied by the transfer protocol) """
	transfer: str = None
	""" The communication protocol used to exchange messages with the endpoint """
	encoding: str = None
	""" Serialization or other form of data encoding to transfer high-level messages over the wire (e.g., json, xml, ...) """
	# Cannot use otupy:URI for uri because it is not guaranteed the correct
	# syntax is used (e.g., the 'scheme', because this is dependent on the
	# discovery mechanism.
	uri: str = None
	""" The base URI used to contact the endpoint (it should include at least the IP address/hostname """
	provider: str = None
	""" Owner of the web service"""

	def __init__(self, description = None, endpoint_type = None, transport = None, 
						transfer = None, encoding = None, uri = None, provider = None):
		self.description = description if description is not None else None
		self.endpoint_type = endpoint_type if endpoint_type is not None else None
		self.transport = transport if transport is not None else None
		self.transfer = transfer if transfer is not None else None
		self.encoding = encoding if encoding is not None else None
		self.uri = uri if uri is not None else None
		self.provider = provider if provider is not None else None

	def __repr__(self):
		return (f"Endpoint(description={self.description}, endpoint_type={self.endpoint_type}, "
	             f"transport={self.transport}, transfer={self.transfer}, encoding={self.encoding}, "
	             f"uri={self.uri},provider={self.provider})")
	
	def __str__(self):
		return self.__repr__()

	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.endpoint_type is not None and not isinstance(self.endpoint_type, str):
			raise TypeError(f"Expected 'endpoint_type' to be of type str, but got {type(self.endpoint_type)}")
		if self.transport is not None and not isinstance(self.transport, L4Proto):
			raise TypeError(f"Expected 'transport' to be of type int, but got {type(self.transport)}")
		if self.transfer is not None and not isinstance(self.transfer, str):
			raise TypeError(f"Expected 'transfer' to be of type int, but got {type(self.transfer)}")
		if self.encoding is not None and not isinstance(self.encoding, str):
			raise TypeError(f"Expected 'encoding' to be of type {str}, but got {type(self.encoding)}")
		if self.uri is not None and not isinstance(self.uri, str):
			raise TypeError(f"Expected 'uri' to be of type {str}, but got {type(self.uri)}")
		if self.provider is not None and not isinstance(self.provider, str):
			raise TypeError(f"Expected 'provider' to be of type {str}, but got {type(self.provider)}")
