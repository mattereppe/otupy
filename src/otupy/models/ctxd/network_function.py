from otupy.models.ctxd.ctxd_object import CTXDObject
from otupy.models.ctxd.network_function_type import NetworkFunctionType


class NetworkFunction(CTXDObject):
	"""Network Function

		A network function process network packets for both forwarding and security purposes.
		It can be hosted on baremetal devices, general purpose computers, containers, and other
		virtualization mechanisms (e.g., Linux namespaces). In these terms, the same model applies
		for both legacy network devices and Network Virtual Functions.
	"""
	type: NetworkFunctionType = None
	""" Type of the network function, including more complex data objects. """
	version: str = None
	""" Version/release of this function """


	def __init__(self, 
			netfun:object = None,
			name:str = None, 
			id:str = None, 
			description:str = None, 
			version:str = None, 
			type:NetworkFunctionType = None):
		if isinstance(netfun, NetworkFunction):
			super().__init__(name=netfun.name, description=netfun.description, id=netfun.id)
			self.version = netfun.version
			self.type = netfun.type
		else:
			super().__init__(name=name, description=description, id=id)
			self.version = str(version) if version is not None else None
			self.type = type 

	def get_subtype(self):
		return self.type.getName()
		
	def __repr__(self):
		return (f"NetworkFunction("
	            f"{super().__repr__()}, "
				  	f"id={self.id}, "
					f"description={self.description}, "
					f"version={self.version}, "
					f"type={self.type.getObj()})")
	
	def __str__(self):
		return self.__repr__()
