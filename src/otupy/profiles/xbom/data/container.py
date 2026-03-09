from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record

class Container(Record):
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

	def __init__(self, container = None, namespace=None, status = None, image = None):
		if container is not None:
			self.namespace = container.namespace
			self.status = container.status
			self.image = container.image
		else:
			self.namespace = str(namespace) if namespace is not None else None
			self.status = str(status) if status is not None else None
			self.image = image 

	def __repr__(self):
		return (f"Container("
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
		# if self.id is not None:
		# 	properties.append(Property(name="otupy:container:id", value=self.id))
		if self.namespace is not None:
			properties.append(Property(name="otupy:container:namespace", value=self.namespace))
		if self.status is not None:
			properties.append(Property(name="otupy:container:status", value=self.status))
		if self.image is not None:
			properties.append(Property(name="otupy:container:image", value=self.image))
		
		return Component(
			name="tmp",
			type=ComponentType.CONTAINER,
			properties=properties
		)

