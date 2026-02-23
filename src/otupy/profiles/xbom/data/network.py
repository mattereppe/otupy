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


	def __init__(self, description = None, name = None, id = None, type = None):
		if isinstance(description, Network):
			self.description = description.description
			self.name = description.name
			self.id = description.id
			self.type = description.type
		else:
			self.description = str(description) if description is not None else None
			self.name = str(name) if name is not None else None
			self.id = str(id) if id is not None else None
			self.type = type if type is not None else None

	def __repr__(self):
		return (f"Network({super().__repr__()}, type={self.type.getObj() if self.type else None})")
	
	def __str__(self):
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
			type_value = self.type.name if hasattr(self.type, 'name') else str(self.type)
			properties.append(Property(name="otupy:network:type", value=type_value))
		
		return Service(
			name=self.name or "unknown",
			bom_ref=generate_bom_ref("network"),
			description=self.description,
			properties=properties
		)

