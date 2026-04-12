from otupy import ArrayOf
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record

class Pod(Record):
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

	def __init__(self, pod:object = None, namespace:str = None):
		if pod is not None:
			self.namespace = pod.namespace
		else:
			self.namespace = str(namespace) 


	def __repr__(self):
		return f"Pod(" \
	            f"namespace={self.namespace}" 
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Pod to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component representation.
		"""
		properties = [
			Property(name="otupy:type", value="pod")
		]
		if self.namespace is not None:
			properties.append(Property(name="otupy:pod:namespace", value=self.namespace))
		
		# Generate a unique bom_ref using centralized generator
		bom_ref = generate_bom_ref("pod")
		
		return Component(
			name="pod",
			type=ComponentType.PLATFORM,
			bom_ref=bom_ref,
			properties=properties
		)	

