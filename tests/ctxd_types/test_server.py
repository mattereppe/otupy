import pytest
import parametrize_from_file

from otupy.types.data.hostname import Hostname
from otupy.profiles.ctxd.data.server import Server


@parametrize_from_file('ctxd_parameters/test_server.yml')
def test_good_parameters(server):
	assert type(Server(server)) == Server

@parametrize_from_file('ctxd_parameters/test_server.yml')
def test_bad_parameters(server):
	with pytest.raises(Exception):
		Server(server)
		Server(Hostname(server))
