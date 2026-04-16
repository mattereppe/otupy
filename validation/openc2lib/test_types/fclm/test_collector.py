import pytest
import parametrize_from_file

from otupy.profiles.fclm.data.collector import Collector
from openc2lib.types.data import IPv4Addr, Port
from otupy.profiles.fclm.data.file_format import FileFormat


@parametrize_from_file("parameters/test_collector.yml")
def test_good_collectors(address, port, format):
    assert isinstance(
        Collector(
            address=IPv4Addr(address) if address else None,
            port=Port(port) if port else None,
            format=FileFormat[format] if format else None,
        ),
        Collector,
    )


@parametrize_from_file("parameters/test_collector.yml")
def test_bad_collectors(address, port, format):
    with pytest.raises(Exception):
        Collector(address=address, port=port, format=format)
