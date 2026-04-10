from otupy.types.base import Record
from otupy.types.data import Port, IPv4Addr


class Collector(Record):
    """
    Collector Class

    Represents a flow exporter/collector configuration.
    - `address`: Optional IPv4 address of the exporter.
    - `port`: Optional port number used by the exporter.
    - `format`: Optional flow export format used by the exporter.
    """

    address: IPv4Addr
    """ IP address of the exporter """

    port: Port = None
    """ Port of the exporter """

    def __init__(self, address: IPv4Addr, port: Port = None):
        super().__init__()
        if address is None:
            raise ValueError("address is required")
        self.address = address
        self.port = port
        self.validate_fields()

    def __repr__(self):
        return f"Collector(address={self.address}, port={self.port})"

    def __str__(self):
        return f"Collector(address={self.address}, port={self.port})"

    def validate_fields(self):
        if self.address is not None and not isinstance(self.address, IPv4Addr):
            raise TypeError(f"Expected 'address' to be ipv4_net, got {type(self.address)}")
        if self.port is not None and not isinstance(self.port, Port):
            raise TypeError(f"Expected 'port' to be Port, got {type(self.port)}")

    def get(self, key, default=None):
        """Mimics dictionary get method"""
        return getattr(self, key, default)
