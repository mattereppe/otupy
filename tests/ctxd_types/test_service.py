import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.peer import Peer
from otupy.types.base.array_of import ArrayOf
from otupy.types.data.version import Version
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.service_type import ServiceType


@parametrize_from_file('ctxd_parameters/test_service.yml')
def test_good_parameters(name, service_type,  subservices, owner, release):
	assert type(Service(name=Name(name),
            		    type=ServiceType(Application()),
						subservices=ArrayOf(Name)(),
						owner=owner,
						release = release)) == Service
	
@parametrize_from_file('ctxd_parameters/test_service.yml')
def test_bad_parameters(name, service_type,  subservices, owner, release):
	with pytest.raises(Exception):
		Service(name=name,
            		    type=ServiceType(Application()),
						subservices=ArrayOf(Name)(),
						owner=owner,
						release = release)



def test_void_application():
	with pytest.raises(Exception):
		Service()
