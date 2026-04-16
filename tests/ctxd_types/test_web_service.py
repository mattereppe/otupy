import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.web_service import WebService
from otupy.profiles.ctxd.data.server import Server
from otupy.types.data.hostname import Hostname


@parametrize_from_file('ctxd_parameters/test_web_service.yml')
def test_good_parameters(description, server, port, endpoint, owner):
	assert type(WebService(description=description,
						server = Server(Hostname(server)),
						port = port,
						endpoint = endpoint,
						owner = owner)) == WebService
	
@parametrize_from_file('ctxd_parameters/test_web_service.yml')
def test_bad_parameters(description, server, port, endpoint, owner):
	with pytest.raises(Exception):
		WebService(description=description,
					server = Server(Hostname(server)),
					port = port,
					endpoint = endpoint,
					owner = owner)



def test_void_application():
	assert type(WebService()) == WebService