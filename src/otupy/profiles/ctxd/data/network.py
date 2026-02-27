from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy.profiles.ctxd.data.network_type import NetworkType
from otupy.profiles.ctxd.data.ctxd_object import CTXDObject


class Network(CTXDObject):
	""" Networking service

		A Network is a service able to transfer packets. There are different types of networks,
		subject to different composition patterns (e.g., physical ethernet, 5G networks, VLAN,
		etc.).
	"""
	type: NetworkType = None
	""" Type of network (Ethernet, veth link, VLAN, ...) """


	def __init__(self, network = None, description = None, name = None, id = None, type = None):
		if isinstance(network, Network):
			super().__init__(name=network.name, description=network.description, id=network.id)
			self.type = network.type
		else:
			super().__init__(name=name, description=description, id=id)
			self.type = type 


	def getId(self, domain=None, namespace=None):
		""" Return a network id 

			The network id includes the network type and list of ip addresses, or any
			other type of network identfiers, if available

		"""
		service_id="net:"+self.type.getName() + "/" + str(domain) + "/" + str(namespace) + "/"

		for n in self.type.getObj().getNets():
			service_id = service_id + "+" + str(n)

		return service_id


	def __repr__(self):
		return (f"Network({super().__repr__()},"
	             f"type={self.type.getObj()})")
	
	def __str__(self):
		return self.__repr__()

