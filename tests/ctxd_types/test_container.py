import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.os import OS




@parametrize_from_file('ctxd_parameters/test_container.yml')
def test_good_parameters(description, container_id, name, namespace, status, image):
	assert type(Container(description,
					   container_id,
					   name,
					   namespace,
						status,
					   image)) == Container
	

@parametrize_from_file('ctxd_parameters/test_container.yml')
def test_bad_parameters(description, container_id, name, namespace, status, image):
	with pytest.raises(Exception):
		Container(description,
					   container_id,
					   name,
					   namespace,
						status,
					   image)
	

def test_void_application():
	assert type(Container()) == Container
