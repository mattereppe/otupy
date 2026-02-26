from otupy import ArrayOf
from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.library import Library
from otupy.profiles.xbom.data.package import Package
from otupy.types.data.hostname import Hostname
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class ExecutionEnvironment(XBOMObject):
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
			libs: ArrayOf(Library)=None,
			pkgs: ArrayOf(Package)=None,
			apps: ArrayOf(Application)=None,
			**kwargs):

		if execenv is not None:
			super().__init__(name=execenv.name, id=execenv.id, description=execenv.description)
			self.apps = execenv.apps
			self.libs = execenv.libs
			self.pkgs = execenv.pkgs
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
			if pkgs is not None:
				self.pkgs = ArrayOf(Package)()
				for pkg in pkgs:
					self.pkgs.append(Package(pkg))

	def __repr__(self):
		return (f"ExecutionEnvironment("
					f"{super().__repr__()},")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert ExecutionEnvironment to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM and nested components.
		"""
		properties = [
			Property(name="otupy:type", value="execution_environment")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:execenv:id", value=self.id))
		
		# Add nested components (applications, libraries, packages)
		nested_components = []
		if self.apps is not None:
			for app in self.apps:
				nested_components.append(app.as_cyclonedx())
		if self.libs is not None:
			for lib in self.libs:
				nested_components.append(lib.as_cyclonedx())
		if self.pkgs is not None:
			for pkg in self.pkgs:
				nested_components.append(pkg.as_cyclonedx())
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("execenv"),
			description=self.description,
			properties=properties,
			components=nested_components if nested_components else None
		)
