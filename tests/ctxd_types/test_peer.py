import pytest
from otupy.profiles.ctxd.data.server import Server
from otupy.types.data.hostname import Hostname
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.consumer import Consumer


@parametrize_from_file('ctxd_parameters/test_peer.yml')
def test_good_parameters(service_name, role, consumer):
	assert type(Peer(service_name,
						role,
						consumer)) == Peer
	
@parametrize_from_file('ctxd_parameters/test_peer.yml')
def test_bad_parameters(service_name, role, consumer):
	with pytest.raises(Exception):
		Peer(service_name,
			role,
			consumer)


def test_void_application():
	assert type(Peer()) == Peer
