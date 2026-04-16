import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.pod import Pod




@parametrize_from_file('ctxd_parameters/test_pod.yml')
def test_good_parameters(description, pod_id, name, namespace, ports):
	assert type(Pod(description=description,
					   id=pod_id,
					   name=name,
					   namespace=namespace,
					   ports=ports)) == Pod
	

@parametrize_from_file('ctxd_parameters/test_pod.yml')
def test_bad_parameters(description, pod_id, name, namespace, ports):
	with pytest.raises(Exception):
		Pod(description=description,
					   id=pod_id,
					   name=name,
					   namespace=namespace,
					   ports=ports)
	

def test_void_application():
	assert type(Pod()) == Pod
