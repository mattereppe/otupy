import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.server import Server
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol


@parametrize_from_file('ctxd_parameters/test_consumer.yml')
def test_good_parameters(host, port, protocol, endpoint, transfer, encoding, profile, actuator):
	assert type(Consumer(host=Server(Hostname(host)),
                    port=port,
                    protocol= protocol,
                    endpoint=endpoint,
                    transfer=transfer,
                    encoding=encoding,
						  profile=profile,
						  actuator=actuator)) == Consumer
	
@parametrize_from_file('ctxd_parameters/test_consumer.yml')
def test_bad_parameters(host, port, protocol, endpoint, transfer, encoding, profile, actuator):
	with pytest.raises(Exception):
		Consumer(host=Server(Hostname(host)),
                    port=port,
                    protocol= protocol,
                    endpoint=endpoint,
                    transfer=transfer,
                    encoding=encoding,
						  profile=profile,
						  actuator=actuator) 



def test_void_application():
	assert type(Consumer()) == Consumer
