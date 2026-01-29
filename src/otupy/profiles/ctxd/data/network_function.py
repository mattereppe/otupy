from otupy import Record
from otupy.profiles.ctxd.data.network_function_type import NetworkFunctionType


class NetworkFunction(Record):
	"""Network Function

		A network function process network packets for both forwarding and security purposes.
		It can be hosted on baremetal devices, general purpose computers, containers, and other
		virtualization mechanisms (e.g., Linux namespaces). In these terms, the same model applies
		for both legacy network devices and Network Virtual Functions.
	"""
	name: str = None
	""" Name of the network function """
	id: str = None
	""" A unique identifier of the function, if available """
	description: str = None
	""" Generic description of the network function """
	type: NetworkFunctionType = None
	""" Type of the network function, including more complex data objects. """
	version: str = None
	""" Version/release of this function """


	def __init__(self, 
			name:str = None, 
			id:str = None, 
			description:str = None, 
			version:str = None, 
			type:NetworkFunctionType = None):
		if isinstance(name, NetworkFunction):
			self.name = name.name
			self.id = name.id
			self.description = name.description
			self.version = name.version
			self.type = name.type
		else:
			self.name = str(name) if name is not None else None
			self.id = str(id) if id is not None else None
			self.description = str(description) if description is not None else None
			self.version = str(id) if id is not None else None
			self.type = type if type is not None else None

	def __repr__(self):
		return (f"NetworkFunction("
	            f"name={self.name}, "
				  	f"id={self.id}, "
					f"description={self.description}, "
					f"version={self.version}, "
					f"type={self.type.getObj()})")
	
	def __str__(self):
		return self.__repr__()
