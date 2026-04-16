import pytest
from otupy.profiles.ctxd.data.application import Application

from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.computer import Computer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.iot import IOT
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.vm import VM
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.web_service import WebService
from otupy.types.data.hostname import Hostname
from otupy.profiles.ctxd.data.service_type import ServiceType


def test_good_parameters():
	assert type(ServiceType(Application())) == ServiceType
	assert type(ServiceType(Computer())) == ServiceType
	assert type(ServiceType(VM())) == ServiceType
	assert type(ServiceType(Pod())) == ServiceType
	assert type(ServiceType(Container())) == ServiceType
	assert type(ServiceType(WebService())) == ServiceType
	assert type(ServiceType(Cloud())) == ServiceType
	assert type(ServiceType(Network())) == ServiceType
	assert type(ServiceType(IOT())) == ServiceType


def test_bad_parameters():
	with pytest.raises(Exception):
		ServiceType()
		ServiceType("prova")
		ServiceType(Hostname("prova"))
