import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.iot import IOT
from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_iot.yml')
def test_good_parameters(description, name, iot_type):
	assert type(IOT(description,
						name,
						iot_type)) == IOT
	
@parametrize_from_file('ctxd_parameters/test_iot.yml')
def test_bad_parameters(description, name, iot_type):
	with pytest.raises(Exception):
		IOT(description,
			name,
			iot_type)



def test_void_application():
	assert type(IOT()) == IOT
