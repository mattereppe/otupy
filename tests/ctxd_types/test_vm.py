import pytest
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.vm import VM



@parametrize_from_file('ctxd_parameters/test_vm.yml')
def test_good_parameters(description, vm_id, name, image):
	assert type(VM(description,
					vm_id,
					name,
					image)) == VM
	
@parametrize_from_file('ctxd_parameters/test_vm.yml')
def test_bad_parameters(description, vm_id, name, image):
	with pytest.raises(Exception):
		VM(description,
			vm_id,
			hostname,
			image)



def test_void_application():
	assert type(VM()) == VM
