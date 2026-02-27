from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment

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
			self.namespace = description.namespace
			self.status = description.status
			self.image = description.image
		else:
			super().__init__(name=name, id=id, description=description)
			self.namespace = str(namespace) if namespace is not None else None
			self.status = str(status) if status is not None else None
			self.image = image if image is not None else None

	def getType(self):
		return "container"

	def __repr__(self):
		return (f"Container({super().__repr__()},"
	             f"namespace={self.namespace}, status={self.status},image={self.image})")
	
	def __str__(self):
		return self.__repr__()
