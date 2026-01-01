"""
	A collection of OpenC2 Actuators built with the otupy framework.
"""
#from otupy.actuators.slpf.mockup_slpf_actuator import MockupSlpfActuator
#from otupy.actuators.slpf.dump_actuator import DumbActuator
from otupy.actuators.ctxd.ctxd_actuator_kubernetes import CTXDActuator_kubernetes
from otupy.actuators.ctxd.ctxd_actuator_openstack import CTXDActuator_openstack
from otupy.actuators.ctxd.ctxd_actuator_docker import CTXDActuator_docker

from otupy.actuators.slpf.slpf_actuator_openstack import SLPFOpenStackActuator
from otupy.actuators.slpf.slpf_actuator_kubernetes import SLPFActuatorKubernetes
from otupy.actuators.slpf.slpf_actuator_iptables import SLPFActuatorIPTables
from otupy.actuators.slpf.slpf_actuator_azure import SLPFActuatorAzure
