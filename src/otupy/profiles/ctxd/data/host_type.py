from otupy import Choice, Register
from otupy.profiles.ctxd.data.vm import VM
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.iot import IoT

class HostType(Choice):
	""" Host device types

		There are different types of Host, which bring more specific info.

	"""

	# This could be further extended with different container types (e.g., docker, containerd)
	register = Register({'server': Server, 'vm': VM, 'pod': Pod, 'iot': IoT})

	def __init__(self, type):
		if(isinstance(type, HostType)):
			super().__init__(type.getObj())
		else:
			super().__init__(type)

	@staticmethod
	def get_type_name(host_type: object):
		""" Get the name associated to a given class
		    
			If the class is not registered, None is returned.
			
			@:param service_type: The class to get the name for.
			@:return: The string used to register the class.
		"""
		return HostType.register.getName(host_type)
