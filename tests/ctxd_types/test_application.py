import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_application.yml')
def test_good_parameters(description, testid, name, version, owner, app_type):
	assert type(Application(description=description,
							id=testid,
						   name=name,
						   version=version,
						   owner=owner,
						   app_type=app_type)) == Application
	
@parametrize_from_file('ctxd_parameters/test_application.yml')
def test_bad_parameters(description, testid, name, version, owner, app_type):
	with pytest.raises(Exception):
		Application(description=description,
							id=testid,
						   name=name,
						   version=version,
						   owner=owner,
						   app_type=app_type)



def test_void_application():
	assert type(Application()) == Application
