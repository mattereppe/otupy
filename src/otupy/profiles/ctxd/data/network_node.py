from otupy.profiles.ctxd.data.ctxd_object import CTXDObject

from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.network_interface import NetworkInterface

class NetworkNode(CTXDObject):
	""" Network node

		A `NetworkNode` is a network slice made of interfaces and IP/MAC addresses. In Linux, such slice is 
		represented by network namespaces. Within a router or switch, there may be other practical implementation
		of network slides.
		
		A `NetworkNode` has one or more network interfaces, which one with network identifiers specific to the
		implemented protocols (e.g., MAC addresses for Ethernet, IP addresses for IP).

		The `NetworkNode` is a subsystem for both ``Host``s and ``ExecutionEnvironment``s. In the first case, 
		it is usually setup by infrastructure managers (e.g., CMS) and typically represents ``physical'' ports 
		available on the hardware. In the second case, it is the collection of network interfaces available in
		the network slice. 

	"""
	ifaces: ArrayOf(NetworkInterface) = None
	""" Network interfaces with addresses"""


	def __init__(self, 
			node:object = None,
			name:str = None, 
			id:str = None, 
			description:str = None, 
			ifaces:ArrayOf(NetworkInterface) = None):
	
		if node is not None:
			super().__init__(name=node.name, id=node.id, description=node.description)
			self.ifaces = node.ifaces
		else:
			super().__init__(name=name, id=id, description=description)
			if ifaces is not None:
				self.ifaces = ArrayOf(NetworkInterface)()
				for iface in ifaces:
					if isinstance(iface, dict):
						self.ifaces.append(NetworkInterface(**iface))
					else:
						self.ifaces.append(NetworkInterface(iface))
			else:
				self.ifaces = None

	def getId(self, domain=None, namespace=None):
		return "ports:" + self.type.getName() + "/" + str(domain) + "/" + str(namespace) + "/" + str(self.name)

	def __repr__(self):
		return (f"NetworkNode("
					f"{super().__repr__()},"
					f"ifaces={self.ifaces})")
	
	def __str__(self):
		return self.__repr__()

