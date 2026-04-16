from otupy.profiles.xbom.data.xbom_object import XBOMObject
import otupy.types.base
from otupy.profiles.xbom.data.network_type import NetworkType
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class Network(XBOMObject):
	"""Network
    it is the description of the service - Network
	"""
	type: NetworkType = None
	""" type of the network service"""
	version: str = None
	""" Version of the network implementation"""


	def __init__(self, network = None, description = None, name = None, id = None, type = None, version=None):
			if isinstance(network, Network):
					super().__init__(name=network.name, description=network.description, id=network.id)
					self.type = network.type
					self.version = network.version
			else:
					super().__init__(name=name, description=description, id=id)
					self.type = type
					self.version = version
	def get_subtype(self):
		return self.type.getName()
	
	def __repr__(self):
		return (f"Network({super().__repr__()},"
                     f"type={self.type.getObj()}, version={self.version})")
		return self.__repr__()

	def as_cyclonedx(self) -> Service:
		"""Convert Network to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="network")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:network:id", value=self.id))
		if self.type is not None:
			type_value = self.get_subtype() if hasattr(self.type, 'getName') else str(self.type)
			properties.append(Property(name="otupy:network:type", value=type_value))
		
		return Service(
			name=self.name or "unknown",
			bom_ref=generate_bom_ref("network"),
			description=self.description,
			properties=properties
		)

