import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.port import Port




@parametrize_from_file('ctxd_parameters/test_port.yml')
def test_good_parameters(description, port_id, iface, addresses, gateway):
	assert type(Port(description,
					   port_id,
					   iface,
					   addresses,
					   gateway)) == Port
	

@parametrize_from_file('ctxd_parameters/test_port.yml')
def test_bad_parameters(description, port_id, iface, addresses, gateway):
	with pytest.raises(Exception):
		Port(description,
			   port_id,
			   iface,
			   addresses,
			   gateway)
	

def test_void_application():
	assert type(Port()) == Port
