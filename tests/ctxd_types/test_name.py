import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.types.data.hostname import Hostname

@parametrize_from_file('ctxd_parameters/test_name.yml')
def test_good_parameters(name):
	assert type(Name(name)) == Name
	assert type(Name(Hostname(name))) == Name

@parametrize_from_file('ctxd_parameters/test_name.yml')
def test_bad_parameters(name):
	with pytest.raises(Exception):
		Name(name)
		Name(LinkType(name))

