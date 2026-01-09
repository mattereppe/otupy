import pytest
from otupy.profiles.ctxd.data.os import OS
import parametrize_from_file

from otupy.profiles.ctxd.data.name import Name


@parametrize_from_file('ctxd_parameters/test_os.yml')
def test_good_parameters(name, version, family, os_type):
	assert type(OS(name,
					version,
					family,
					os_type)) == OS


def test_void_application():
	assert type(OS()) == OS
