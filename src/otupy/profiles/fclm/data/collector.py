from otupy.types.base import Record, Choice
from otupy.types.data import Port, IPv4Addr, IPv6Addr, Hostname
from otupy.core.extensions import Register
from otupy.profiles.fclm.data.file_format import FileFormat

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
            super().__init__(host.getObj())
        elif (isinstance(host, str)):
			# Use as hostname, the safest option
            super().__init__(Hostname(host))
        else:
            # Will fail if a wrong input type is provided
            super().__init__(host)

    def __repr__(self):
        """ Return the internal object value """
        return str(self.getObj())

    def __str__(self):
        """ Return the internal representation"""
        return self.__repr__()



class Collector(Record):
    """
    Collector Class

    Represents a flow collector configuration.
	 :param host: Address/name of the exporter. Default: 127.0.0.1
    :param port: Port number used by the exporter. Default: 2055
    :param format: Optional flow export format used by the collector.
    """

    host: Host = None
    """ IP address of the collector """

    port: Port = None
    """ Port of the collector """

    format: FileFormat = None
    """ Flow export file format (e.g., JSON, YAML, etc.) """

    def __init__(self, host: Host = "127.0.0.1", port: Port = 5044, format: FileFormat = None):
        super().__init__()
        self.host = Host(host)
        self.port = port
        self.format = format
        self.validate_fields()

    def __repr__(self):
        return f"Collector(host={self.host}, port={self.port}, format={self.format})"

    def __str__(self):
        return f"Collector(host={self.host}, port={self.port}, format={self.format})"

    def validate_fields(self):
        if self.host is not None and not isinstance(self.host, Host):
            raise TypeError(f"Expected 'host' to be Host, got {type(self.host)}")
        if self.port is not None and not isinstance(self.port, Port):
            raise TypeError(f"Expected 'port' to be Port, got {type(self.port)}")
        if self.format is not None and not isinstance(self.format, FileFormat):
            raise TypeError(f"Expected 'format' to be FileFormat, got {type(self.format)}")

    def get(self, key, default=None):
        """Mimics dictionary get method"""
        return getattr(self, key, default)
