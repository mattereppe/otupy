from otupy.types.base import Record

class Container(Record):
	""" Container

		A container is a software image run in with linux namespace sandbox or similar technology.
		A container is an execution environment made of its own subsystems (network interfaces, file 
		systems, etc.). There are not part of the container model, but will be included as part
		of the container service.

		Other definitions could be used for specific Container technologies (i.e., Docker).
	"""
	namespace: str = None
	""" Namespace of the Container"""
	status: str = None
	""" Current status of the Container"""
	image: str = None
	""" Image used by the Container """

	def __init__(self, container = None, namespace=None, status = None, image = None):
		if container is not None:
			self.namespace = description.namespace
			self.status = description.status
			self.image = description.image
		else:
			self.namespace = str(namespace) if namespace is not None else None
			self.status = str(status) if status is not None else None
			self.image = image 


	def __repr__(self):
		return (f"Container("
	             f"namespace={self.namespace}, status={self.status},image={self.image})")
	
	def __str__(self):
		return self.__repr__()
