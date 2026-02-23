from otupy.profiles.xbom.data.execution_environment import ExecutionEnvironment
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class OS(ExecutionEnvironment):
	"""OS
    Operating System
    
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


	def __init__(self, os=None, version=None, family=None, arch=None, **kwargs):
		if os is not None and isinstance(os, OS):
			super().__init__(os)
			self.version = os.version
			self.family = os.family
			self.arch = os.arch
		else:
			super().__init__(**kwargs)
			self.version = str(version) if version is not None else None
			self.family = str(family) if family is not None else None
			self.arch = str(arch) if arch is not None else None

	def __repr__(self):
		return (f"OS({super().__repr__()}, "
	             f"version={self.version}, family={self.family}, arch={self.arch})")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert OS to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type OPERATING_SYSTEM.
		"""
		properties = [
			Property(name="otupy:type", value="os")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:os:id", value=self.id))
		if self.family is not None:
			properties.append(Property(name="otupy:os:family", value=self.family))
		if self.arch is not None:
			properties.append(Property(name="otupy:os:arch", value=self.arch))
		
		# Include nested components from ExecutionEnvironment
		nested_components = []
		if self.libs:
			for lib in self.libs:
				if hasattr(lib, 'as_cyclonedx'):
					nested_components.append(lib.as_cyclonedx())
		if self.pkgs:
			for pkg in self.pkgs:
				if hasattr(pkg, 'as_cyclonedx'):
					nested_components.append(pkg.as_cyclonedx())
		if self.apps:
			for app in self.apps:
				if hasattr(app, 'as_cyclonedx'):
					nested_components.append(app.as_cyclonedx())
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.OPERATING_SYSTEM,
			bom_ref=generate_bom_ref("os"),
			version=self.version,
			description=self.description,
			components=nested_components if nested_components else None,
			properties=properties
		)


