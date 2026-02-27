from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy.profiles.ctxd.data.network_type import NetworkType


class Network(CTXDObject):
	""" Network
		
		This is a generic network description, including different types of virtual and physical networks.
	"""
	type: NetworkType = None
	""" type of the network service"""


	def __init__(self, network = None, description = None, name = None, id = None, type = None):
		if isinstance(network, Network):
			super().__init__(name=network.name, description=network.description, id=network.id)
			self.type = network.type
		else:
			super().__init(name=name, description=description, id=id)
			self.type = type 


	def getId(self, domain=None, namespace=None):
		""" Return a network id 

			The network id includes the network type and list of ip addresses, or any
			other type of network identfiers, if available

		"""
		service_id="net:"+self.type.getName() + "/" + str(domain) + "/" + str(namespace) + "/"

		for n in type.getObj().getNets():
			service_id = service_id + "+" + str(n)

		return service_id


	def __repr__(self):
		return (f"Network(description={self.description}, "
	             f"name={self.name}, id={self.id}, type={self.type.getObj()})")
	
	def __str__(self):
		return f"Network(" \
	            f"description={self.description}, " \
	            f"name={self.name}, " \
					f"id={self.id}, " \
	            f"type={self.type.getObj()})"

