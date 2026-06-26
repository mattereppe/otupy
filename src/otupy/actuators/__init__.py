"""
	Otupy actuators for security functions

	A collection of OpenC2 Actuators built with the otupy framework. Actuators are grouped by the specific profile they implement.
	It is not recommended to buid actuators for multiple profiles; if a security function falls under the scope of multiple profiles,
	a different actuator should be created for each profile.

"""
from otupy.actuators.slpf.mockup_slpf_actuator import MockupSlpfActuator
from otupy.actuators.slpf.dumb_actuator import DumbActuator
from otupy.actuators.xbom.xbom_actuator_kubernetes import XBOMKubernetesActuator
from otupy.actuators.xbom.xbom_actuator_openstack import XBOMOpenStackActuator
from otupy.actuators.xbom.xbom_actuator_host import XBOMHostActuator
from otupy.actuators.xbom.xbom_actuator_file import XBOMFileActuator
from otupy.actuators.xbom.xbom_actuator_docker import XBOMDockerActuator
from otupy.actuators.xbom.xbom_actuator_open5gs import XBOMOpen5gsActuator

from otupy.actuators.slpf.slpf_actuator_openstack import SLPFOpenStackActuator
from otupy.actuators.slpf.slpf_actuator_kubernetes import SLPFActuatorKubernetes
from otupy.actuators.slpf.slpf_actuator_iptables import SLPFActuatorIPTables
from otupy.actuators.slpf.slpf_actuator_azure import SLPFActuatorAzure

from otupy.actuators.nfm.nfm_actuator_fprobe import NFMActuatorFProbe
from otupy.actuators.nfm.nfm_actuator_nprobe import NFMActuatorNProbe
from otupy.actuators.nfm.nfm_actuator_packetbeat import NFMActuatorPacketbeat
from otupy.actuators.fclm.fclm_actuator_filebeat import FCLMActuatorFilebeat
