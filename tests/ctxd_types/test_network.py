import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_network.yml')
def test_good_parameters(description, name, network_type):
	assert type(Network(description,
						name,
						network_type)) == Network
	


def test_void_application():
	assert type(Network()) == Network
