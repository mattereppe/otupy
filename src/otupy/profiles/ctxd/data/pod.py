from otupy import ArrayOf
from otupy.profiles.ctxd.data.host import Host

class Pod(Host):
	""" Kubernetes pod
		
		A pod is the logical unit in Kubernetes to run one or more containers. Other
		orchestration tool does not have this concept. 
		
		The concrete implementation of a Kubernetes Pod is a network namespace (in Linux).
		More than one containers can be hosted inside a Pod, each sharing the same
		network interface but with its own pid and filesystem namespaces. In this respect,
		the Pod does not provide totally isolated environments like other virtualisation
		models (i.e., virtual machines), because for containers inside the same Pod
		there is an overlapping of the network namespace. Indeed, the Pod is more a 
		management unit than a true isolation environment. However, since multiple
		containers in the same Pod are often used as sidecars for network operations
		(e.g., TLS/SSL proxy), we consider the Pod as a lightweight virtualised Host, 
		which is necessary to maintain consistency with the Host-ExecutionEnvironment 
		hierarchy we are implementing.
		
		As any other ``Host``, the Pod is expected to have internal subsystems for the
		network, filesystems, etc.

	"""
	namespace: str = None
	""" Namespace where the pod is instantiated """

	def __init__(self, pod:object = None, namespace:str = None, **kwargs):
		if isinstance(pod, Pod):
			super().__init(pod)
			self.namespace = pod.namespace
		else:
			super().__init__(**kwargs)
			self.namespace = str(namespace) 

	def getType(self):
		return "pod"

	def __repr__(self):
		return f"Pod(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"namespace={self.namespace}, " \
				f"ports={self.ports})" 
	
	def __str__(self):
		return self.__repr__()
	
