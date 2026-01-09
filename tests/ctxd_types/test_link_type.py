import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.link_type import LinkType


@parametrize_from_file('ctxd_parameters/test_link_type.yml')
def test_good_parameters(link_type):
	assert type(LinkType(link_type)) == LinkType
	
@parametrize_from_file('ctxd_parameters/test_link_type.yml')
def test_bad_parameters(link_type):
	with pytest.raises(Exception):
		LinkType(link_type)

