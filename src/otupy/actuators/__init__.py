"""
	Otupy actuators for security functions

	A collection of OpenC2 Actuators built with the otupy framework. Actuators are grouped by the specific profile they implement.
	It is not recommended to buid actuators for multiple profiles; if a security function falls under the scope of multiple profiles,
	a different actuator should be created for each profile.

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

from otupy.actuators.xbom.xbom_actuator_kubernetes import XBOMActuator_kubernetes
from otupy.actuators.xbom.xbom_actuator_openstack import XBOMActuator_openstack
from otupy.actuators.xbom.xbom_actuator_docker import XBOMActuator_docker
