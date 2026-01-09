import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_cloud.yml')
def test_good_parameters(description, cloud_id, name, cloud_type):
	assert type(Cloud(description,
						cloud_id,
						name,
						cloud_type)) == Cloud
	
@parametrize_from_file('ctxd_parameters/test_cloud.yml')
def test_bad_parameters(description, cloud_id, name, cloud_type):
	with pytest.raises(Exception):
		Cloud(description,
				cloud_id,
				name,
				cloud_type)



def test_void_application():
	assert type(Cloud()) == Cloud
