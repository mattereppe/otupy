import otupy.types.base

class Container(otupy.types.base.Record):
	""" Container

		A container is a software image run in with linux namespace sandbox or similar technology.
		A container might be directly run (as in docker) or part of a higher abstraction (the pod,
		as in Kubernetes). Containers are often grouped into namespaces, but this is not necessary
		for Kubernetes, where the namespace concept applies to pods.
	"""
	description: str = None
	""" Generic description of the Container """
	id: str = None
	""" ID of the Container """
	name: str = None
	""" Name of the Container"""
	namespace: str = None
	""" Namespace of the Container"""
	status: str = None
	""" Current status of the Container"""
	image: str = None
	""" Image used by the Container """

	def __init__(self, description = None, id = None, name = None, namespace=None, status = None, image = None):
		if isinstance(description, Container):
			self.description = description.description
			self.id = description.id
			self.name = description.name
			self.namespace = description.namespace
			self.status = description.status
			self.image = description.image
		else:
			self.description = str(description) if description is not None else None
			self.id = str(id) if id is not None else None
			self.name = str(name) if name is not None else None
			self.namespace = str(namespace) if namespace is not None else None
			self.status = str(status) if status is not None else None
			self.image = image if image is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Container(description={self.description}, id={self.id}, "
	             f"name={self.name}, namespace={self.namespace}, status={self.status},image={self.image})")
	
	def __str__(self):
		return f"Container(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"namespace={self.namespace}, " \
				f"status={self.status}, " \
	            f"image={self.image})"
	
	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")		
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type {str}, but got {type(self.name)}")
		if self.namespace is not None and not isinstance(self.namespace, str):
			raise TypeError(f"Expected 'namespace' to be of type {str}, but got {type(self.namespace)}")
		if self.status is not None and not isinstance(self.status, str):
			raise TypeError(f"Expected 'status' to be of type {str}, but got {type(self.status)}")	
		if self.image is not None and not isinstance(self.image, str):
			raise TypeError(f"Expected 'image' to be of type {str}, but got {type(self.image)}")

