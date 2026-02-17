from otupy import ArrayOf
from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.library import Library
from otupy.profiles.ctxd.data.package import Package
from otupy.types.data.hostname import Hostname

class ExecutionEnvironment(CTXDObject):
	""" Execution Environment
   	
	  The ExecutionEnvironment  model abstracts a set of software resources
	  that allow to run an application. This typically includes a pid space,
	 	a filesystem, a network slice, etc. There will be multiple child classes
		of an execution environment, which will define typical cases, like a full 
		Operating System, a container, a Python venv, a chroot, etc.

		An Execution Environment could be hosted on real or physical hardware
		(Host, Virtual Machine, IoT device), or
		inside another ExecutionEnvironment, which typically happens for containers
		and other software environments.

		In general, we expect applications or libraries to be present to support the execution
		of other software.
	"""
	libs: ArrayOf(Library) = None
	""" List of libraries installed in this ExecutionEnvironment """
	pkgs: ArrayOf(Package) = None
	""" List of packages instsalled (for package-based systems) """
	apps: ArrayOf(Application) = None
	""" List of applications installed on this ExecutionEnvironment """

	def __init__(self, execenv: object = None, 
			description:str = None, 
			id:str = None, 
			name:Hostname = None, 
			libs: ArrayOf(Library)=None,
			apps: ArrayOf(Application)=None,
			**kwargs):

		if execenv is not None:
			super().__init__(name=execenv.name, id=execenv.id, description=execenv.description)
			self.apps = execenv.apps
			self.libs = execenv.libs
		else:
			super().__init__(name=name, id=id, description=description)
			if apps is not None:
				self.apps = ArrayOf(Application)()
				for app in apps:
					self.apps.append(Application(app))
			if libs is not None:
				self.libs = ArrayOf(Library)()
				for lib in libs:
					self.libs.append(Library(lib))

	def __repr__(self):
		return (f"ExecutionEnvironment("
					f"{super().__repr__()},")
	
	def __str__(self):
		return self.__repr__()

