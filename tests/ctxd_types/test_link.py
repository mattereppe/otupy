import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.peer import Peer
from otupy.types.base.array_of import ArrayOf
from otupy.types.data.version import Version


@parametrize_from_file('ctxd_parameters/test_link.yml')
def test_good_parameters(name, description, versions, link_type, peers ):
	assert type(Link(name=Name(name),
            		    description=description,
                        versions=versions,
                    	link_type=link_type,
                        peers=peers ))== Link
	
@parametrize_from_file('ctxd_parameters/test_link.yml')
def test_bad_parameters(name, description, versions, link_type, peers):
	with pytest.raises(Exception):
		Link(name=name,
            	description=description,
                versions=versions,
            	link_type=link_type,
                peers=peers)



def test_void_application():
	assert type(Link()) == Link
