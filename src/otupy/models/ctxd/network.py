from otupy.models.ctxd.ctxd_object import CTXDObject
from otupy.models.ctxd.network_type import NetworkType
from otupy.models.ctxd.ctxd_object import CTXDObject


class Network(CTXDObject):
	""" Networking service

		A Network is a service able to transfer packets. There are different types of networks,
		subject to different composition patterns (e.g., physical ethernet, 5G networks, VLAN,
		etc.).
	"""
	type: NetworkType = None
	""" Type of network (Ethernet, veth link, VLAN, ...) """
	version: str = None
	""" Version of the network implementation"""


	def __init__(self, network = None, description = None, name = None, id = None, type = None, version=None):
		if isinstance(network, Network):
			super().__init__(name=network.name, description=network.description, id=network.id)
			self.type = network.type
			self.version=network.version
		else:
			super().__init__(name=name, description=description, id=id)
			self.type = type 
			self.version=version


	def get_subtype(self):
		return self.type.getName()

	def __repr__(self):
		return (f"Network({super().__repr__()},"
                     f"type={self.type.getObj()}, version={self.version})")
		return self.__repr__()

