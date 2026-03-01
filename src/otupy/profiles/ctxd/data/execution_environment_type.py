from otupy import Choice, Register
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.os import OS

class ExecutionEnvironmentType(Choice):
	""" Execution environment types

		There are different types of ExecutionEnvironments, which bring more specific info.

	"""

	# This could be further extended with different container types (e.g., docker, containerd)
	register = Register({'container': Container, 'os': OS})

	def __init__(self, type):
		if(isinstance(type, ExecutionEnvironmentType)):
			super().__init__(type.getObj())
		else:
			super().__init__(type)

	@staticmethod
	def get_type_name(execenv_type: object):
		""" Get the name associated to a given class
		    
			If the class is not registered, None is returned.
			
			@:param service_type: The class to get the name for.
			@:return: The string used to register the class.
		"""
		return ExecutionEnvironmentType.register.getName(execenv_type)
