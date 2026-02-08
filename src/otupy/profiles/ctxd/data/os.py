from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment

class OS(ExecutionEnvironment):
	""" Operating System

		The Operating System is one common Execution Environment, which
		can execute almost any software. It will have a full set of libraries
		and applications, as well as many subsystems (file systems, etc.).

	"""
	version: str = None
	""" Version of the OS """
	family: str = None
	""" Family of the OS """
	arch: str = None
	""" Supported CPU architecture """


	def __init__(self, os = None, 
			version = None, family = None, arch = None,
			**kwargs):
		if os is not None:
			super().__init__(os=os)
			self.version=os.version
			self.family=os.family
			self.arch=os.family
		else:
			super().__init__(**kwargs)
			self.version = str(version) 
			self.family = str(family) 
			self.arch = str(arch)

	def __repr__(self):
		return (f"OS({super().__repr__()},"
	             f"version={self.version}, family={self.family}, type={self.arch})")
	
	def __str__(self):
		return self.__repr__()

