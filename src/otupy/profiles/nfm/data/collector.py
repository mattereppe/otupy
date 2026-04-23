from otupy.types.base import Record, Choice
from otupy.types.data import Port, IPv4Addr, IPv6Addr
from otupy.core.extensions import Register

class Host(Choice):
	""" 	Collector host identifier

		A container for different types of identifiers.
		Currently supported: IP, hostname.
		
		For internal use only, not intended to be exposed
		to other classes
	"""
    register = Register({'hostname': Hostname, 'ipv4': IPv4Addr, 'ipv6': IPv6Addr})

    def __init__(self, host):
        """ Instantiate a host identifier
        
           It checks the type of the input parameter to perform the correct instantiation

          :param host: The identifier of the host (could be a Host, IPv4Addr, IPv6Addr, Hostname, str)
        """
        if(isinstance(host, Host)):
            super().__init__(host.obj)
        elif (isinstance(host, str)):
			# Use as hostname, the safest option
            host = Hostname(host)
        else:
            # Will fail if a wrong input type is provided
            super().__init__(host)

   def __repr__(self):
      """ Return the internal object value """
      return self.getObj()

   def __str__(self):
      """ Return the internal representation"""
      return self.__repr__()


class Collector(Record):
    """
    Collector Class

    Represents a flow exporter/collector configuration.
	
	 :param host: Address/name of the exporter. Default: 127.0.0.1
    :param port: Port number used by the exporter. Default: 2055
    """

    host: Host
    """ Name/address of the exporter """

    port: Port = None
    """ Port of the exporter """

    def __init__(self, host: Host = "127.0.0.1", port: Port = 2055):
        super().__init__()
        self.host = host
        self.port = port
        self.validate_fields()

    def __repr__(self):
        return f"Collector(host={self.host}, port={self.port})"

    def __str__(self):
        return f"Collector(host={self.host}, port={self.port})"

    def validate_fields(self):
        if self.host is not None and not isinstance(self.host, Host):
            raise TypeError(f"Expected 'Host' to be Host, got {type(self.Host)}")
        if self.port is not None and not isinstance(self.port, Port):
            raise TypeError(f"Expected 'port' to be Port, got {type(self.port)}")

    def get(self, key, default=None):
        """Mimics dictionary get method"""
        return getattr(self, key, default)
