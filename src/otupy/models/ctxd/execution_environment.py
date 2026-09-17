from otupy import ArrayOf
from otupy.models.ctxd.ctxd_object import CTXDObject
from otupy.models.ctxd.execution_environment_type import ExecutionEnvironmentType
from otupy.models.ctxd.application import Application
from otupy.models.ctxd.library import Library
from otupy.models.ctxd.package import Package
from otupy.types.data.hostname import Hostname

class ExecutionEnvironment(CTXDObject):
	""" Execution Environment
   	
	  The ExecutionEnvironment  model abstracts a set of software resources
	  that allow to run an application. The latter typically include a pid space,
	 	a filesystem, a network slice, etc. There will be multiple child classes
		of an execution environment, which will define typical cases, like a full 
		Operating System, a container, a Python venv, a chroot, etc.

		An Execution Environment is hosted on a Host, which could any physical or virtual hardware,
		including physical servers, virtual machines, IoT devices, Kubernetes pods, etc. 

		An ``ExecutionEnvironment`` will typically be made of several subsystems for file systems,
		network slices, etc. This approach enables to provide a hierarchical view of components
		and subcomponents, including links at different layers.
	

		In general, we expect applications or libraries to be present to support the execution
		of other software.
	"""
	version:str = None
	""" Version of this Execution environment"""
	type: ExecutionEnvironmentType = None
	""" Specific type of Execution Environment """
	libs: ArrayOf(Library) = None
	""" List of libraries installed in this ExecutionEnvironment """
	pkgs: ArrayOf(Package) = None
	""" List of packages installed (for package-based systems) """
	apps: ArrayOf(Application) = None
	""" List of applications installed on this ExecutionEnvironment """

	def __init__(self, execenv: object = None, 
			description:str = None, 
			id:str = None, 
			name:Hostname = None, 
			version:str = None,
			type:ExecutionEnvironmentType = None,
			libs: ArrayOf(Library)=None,
			pkgs: ArrayOf(Package)=None,
			apps: ArrayOf(Application)=None,
			**kwargs):

		if execenv is not None:
			super().__init__(name=execenv.name, id=execenv.id, description=execenv.description)
			self.version = execenv.version
			self.type = execenv.type
			self.apps = execenv.apps
			self.pkgs = execenv.pkgs
			self.libs = execenv.libs
		else:
			super().__init__(name=name, id=id, description=description)
			self.version = version
			self.type = type
			if apps is not None:
				self.apps = ArrayOf(Application)()
				for app in apps:
					self.apps.append(Application(app))
			if pkgs is not None:
				self.pkgs = ArrayOf(Package)()
				for pkg in pkgs:
					self.pkgs.append(Package(pkg))
			if libs is not None:
				self.libs = ArrayOf(Library)()
				for lib in libs:
					self.libs.append(Library(lib))

	def get_subtype(self):
		return self.type.getName()

	def __repr__(self):
		return (f"ExecutionEnvironment("
					f"{super().__repr__()},"
					f"version={self.version},"
					f"type={self.type.getObj().__repr__()}")
	
	def __str__(self):
		return self.__repr__()

