from otupy.profiles.xbom.data.execution_environment import ExecutionEnvironment
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Container(ExecutionEnvironment):
	""" Container

		A container is a software image run in with linux namespace sandbox or similar technology.
		A container is an execution environment made of its own subsystems (network interfaces, file 
		systems, etc.). There are not part of the container model, but will be included as part
		of the container service.
	"""
	namespace: str = None
	""" Namespace of the Container"""
	status: str = None
	""" Current status of the Container"""
	image: str = None
	""" Image used by the Container """

	def __init__(self, container = None, description = None, id = None, name = None, 
			namespace=None, status = None, image = None):
		if container is not None:
			super().__init__(name=container.name, id=container.id, description=container.description)
			self.namespace = container.namespace
			self.status = container.status
			self.image = container.image
		else:
			super().__init__(name=name, id=id, description=description)
			self.namespace = str(namespace) if namespace is not None else None
			self.status = str(status) if status is not None else None
			self.image = image if image is not None else None

	def __repr__(self):
		return (f"Container({super().__repr__()},"
	             f"namespace={self.namespace}, status={self.status},image={self.image})")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Container to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type CONTAINER.
		"""
		properties = [
			Property(name="otupy:type", value="container")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:container:id", value=self.id))
		if self.namespace is not None:
			properties.append(Property(name="otupy:container:namespace", value=self.namespace))
		if self.status is not None:
			properties.append(Property(name="otupy:container:status", value=self.status))
		if self.image is not None:
			properties.append(Property(name="otupy:container:image", value=self.image))
		
		# Add nested components from ExecutionEnvironment (apps, libs, pkgs)
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
			type=ComponentType.CONTAINER,
			bom_ref=generate_bom_ref("container"),
			description=self.description,
			properties=properties,
			components=nested_components if nested_components else None
		)

