""" SLPF actuators

	This folder groups actuators that implement the ``slpf`` profile. 
	They include a few "dump" actuators that can be used to test the query method,
	but does not act on any firewall

	TODO: Add supported actuators.
"""

from otupy.actuators.slpf.dumb_actuator import DumbActuator
from otupy.actuators.slpf.mockup_slpf_actuator import MockupSlpfActuator
