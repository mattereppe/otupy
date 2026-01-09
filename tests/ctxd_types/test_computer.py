import pytest
from otupy.profiles.ctxd.data.computer import Computer
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_computer.yml')
def test_good_parameters(description, computer_id, hostname, os, apps):
	assert type(Computer(description,
					computer_id,
					hostname,
					os,
					apps)) == Computer

@parametrize_from_file('ctxd_parameters/test_computer.yml')
def test_bad_parameters(description, computer_id, hostname, os, apps):
	with pytest.raises(Exception):
		Computer(description,
					computer_id,
					hostname,
					os,
					apps)


def test_void_application():
	assert type(Computer()) == Computer
