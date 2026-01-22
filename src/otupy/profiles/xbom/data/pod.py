from otupy.types.base import Record, ArrayOf
from otupy.profiles.xbom.data.port import Port
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Pod(Record):
	""" Kubernetes pod
		
		A pod is the logical unit in Kubernetes to run one or more containers. Other
		orchestration tool does not have this concept.

	"""
	description: str = None
	""" Generic description of the Container """
	id: str = None
	""" ID of the Pod """
	name: str = None
	""" Name of the Pod"""
	namespace: str = None
	""" Namespace where the pod is instantiated """
	ports: ArrayOf(Port) = None
	""" Network interfaces of the Pod"""

	def __init__(self, description = None, id = None, name = None, namespace = None, ports = None):
		if isinstance(description, Pod):
			self.description = description.description
			self.id = description.id
			self.name = description.name
			self.namespace = description.namespace
			self.ports = description.ports
		else:
			self.description = str(description) if description is not None else None
			self.id = str(id) if id is not None else None
			self.name = str(name) if name is not None else None
			self.namespace = str(namespace) if namespace is not None else None
			self.ports = ArrayOf(Port)(ports) if ports is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Pod(description={self.description}, id={self.id}, "
	             f"name={self.name}, namespace={self.namespace}, ports={self.ports})")
	
	def __str__(self):
		return f"Pod(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"namespace={self.namespace}, " \
				f"ports={self.ports}" 
	
	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")		
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type {str}, but got {type(self.name)}")
		if self.namespace is not None and not isinstance(self.namespace, str):
			raise TypeError(f"Expected 'namespace' to be of type {str}, but got {type(self.namespace)}")
		if self.ports is not None and not issubclass(type(self.ports), list):
			raise TypeError(f"Expected 'ports' to be of type {ArrayOf(Port)}, but got {type(self.ports)}")

	def as_cyclonedx(self) -> Service:
		"""Convert Pod to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="pod")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:pod:id", value=self.id))
		if self.namespace is not None:
			properties.append(Property(name="otupy:pod:namespace", value=self.namespace))
		
		# Add port properties
		if self.ports is not None:
			for port in self.ports:
				port_props = port.as_cyclonedx()
				properties.extend(port_props)
		
		# Generate a unique bom_ref using centralized generator
		bom_ref = generate_bom_ref("pod")
		
		return Service(
			name=self.name or "unknown",
			bom_ref=bom_ref,
			description=self.description,
			properties=properties
		)	

