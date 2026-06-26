import pytest
import parametrize_from_file

from otupy.profiles.fclm.data.collector import Collector, Host
from otupy.types.data import IPv4Addr, Port
from otupy.profiles.fclm.data.file_format import FileFormat


# TODO: Add good/bad parameters for hostname/IPv6 addresses
@parametrize_from_file("parameters/test_collector.yml")
def test_good_collectors(address, port, format):
    assert isinstance(
        Collector(
            host=Host(IPv4Addr(address)) if address else Host(''),
            port=Port(port) if port else None,
            format=FileFormat[format] if format else None,
        ),
        Collector,
    )


@parametrize_from_file("parameters/test_collector.yml")
def test_bad_collectors(address, port, format):
    with pytest.raises(Exception):
        Collector(address=Host(IPv4Addr(address)), port=port, format=format)
