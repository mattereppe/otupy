from otupy.profiles.ctxd.data.ctxd_object import CTXDObject

from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.port import Port

class NetworkNode(CTXDObject):
	""" Network node

		A `NetworkNode` is a network slice made of interfaces and IP/MAC addresses. In Linux, such slice is 
		represented by network namespaces. Within a router or switch, there may be other practical implementation
		of network slides.
		
		
		ny kind of entity attached to the network. The scope includes both network
		equipment (routers, switches, access points) and hosts (computers attached to a network). .
		A `NetworkNode` has one or more network ports, which one with network identifiers specific to the
		implemented protocols (e.g., MAC addresses for Ethernet, IP addresses for IP).

		The `NetworkNode` represents a base class to derive more specific classes for network equipment and
		hosts, hosting the common network-related characteristics (namely, network ports). It can be used alone
		when it is a subsystem inside a bigger system, for instance a Linux network namespace, or when the 
		underlying implementation is not known (for instance, a router which concrete implementation is not know).

	"""
	ports: ArrayOf(Port) = None
	""" Network interfaces with addresses"""


	def __init__(self, 
			node:object = None,
			name:str = None, 
			id:str = None, 
			description:str = None, 
			ports:ArrayOf(Port) = None):
	
		if node is not None:
			super().__init__(name=node.name, id=node.id, description=node.description)
			self.ports = name.ports
		else:
			super().__init__(name=name, id=id, description=description)
			if ports is not None:
				self.ports = ArrayOf(Port)()
				for port in ports:
					if isinstance(port, dict):
						self.ports.append(Port(**port))
					else:
						self.ports.append(Port(port))
			else:
				self.ports = None

	def __repr__(self):
		return (f"NetworkNode("
					f"{super().__repr__()},"
					f"ports={self.ports})")
	
	def __str__(self):
		return self.__repr__()

