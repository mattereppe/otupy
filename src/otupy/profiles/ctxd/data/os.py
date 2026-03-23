from otupy.types.base import Record

class OS(Record):
	""" Operating System

		The Operating System is one common Execution Environment, which
		can execute almost any software. It will have a full set of libraries
		and applications, as well as many subsystems (file systems, etc.).

	"""
	family: str = None
	""" Family of the OS """
	version: str = None
	""" Version of the OS """
	release: str = None
	""" Release number/string """
	arch: str = None
	""" Supported CPU architecture """


	def __init__(self, os = None, version = None, family = None, release=None,  arch = None):
		if os is not None:
			self.family=os.family
			self.version=os.version
			self.release=os.release
			self.arch=os.family
		else:
			self.family = str(family) 
			self.version = str(version) 
			self.release = str(release) 
			self.arch = str(arch)


	def __repr__(self):
		return (f"OS("
	             f"family={self.family}, version={self.version}, release={self.release}, type={self.arch})")
	
	def __str__(self):
		return self.__repr__()

