from otupy import ArrayOf
from otupy.profiles.ctxd.data.network_node import NetworkNode

class Pod(NetworkNode):
	""" Kubernetes pod
		
		A pod is the logical unit in Kubernetes to run one or more containers. Other
		orchestration tool does not have this concept. Basically, it is a networked
		container for software, so it plays the role of a `NetworkNode`.

		It inherits the following attributes from the NetworkNode:

		- ``name`` (``Hostname``)
		- ``description`` (``str``)
		- ``id`` (``str``)
		- ``ports`` (``Port``)

	"""
	namespace: str = None
	""" Namespace where the pod is instantiated """

	def __init__(self, namespace:str = None, **kwargs):
		if isinstance(namespace, Pod):
			super().__init(namespace)
			self.namespace = namespace.namespace
		else:
			super().__init__(**kwargs)
			self.namespace = str(namespace) 
		self.validate_fields()

	def __repr__(self):
		return f"Pod(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"namespace={self.namespace}, " \
				f"ports={self.ports})" 
	
	def __str__(self):
		return self.__repr__()
	
	def validate_fields(self):
		if self.namespace is not None and not isinstance(self.namespace, str):
			raise TypeError(f"Expected 'namespace' to be of type {str}, but got {type(self.namespace)}")

