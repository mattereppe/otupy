import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.peer_role import PeerRole


@parametrize_from_file('ctxd_parameters/test_peer_role.yml')
def test_good_parameters(peer_role):
	assert type(PeerRole(peer_role)) == PeerRole
	
@parametrize_from_file('ctxd_parameters/test_peer_role.yml')
def test_bad_parameters(peer_role):
	with pytest.raises(Exception):
		PeerRole(peer_role)

