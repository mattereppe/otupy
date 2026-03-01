from otupy.types.base import Record

class OS(Record):
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


	def __init__(self, os = None, version = None, family = None, arch = None):
		if os is not None:
			self.version=os.version
			self.family=os.family
			self.arch=os.family
		else:
			self.version = str(version) 
			self.family = str(family) 
			self.arch = str(arch)


	def __repr__(self):
		return (f"OS("
	             f"version={self.version}, family={self.family}, type={self.arch})")
	
	def __str__(self):
		return self.__repr__()

