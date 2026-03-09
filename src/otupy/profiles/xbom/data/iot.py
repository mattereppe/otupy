from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record


class IOT(Record):
	"""IOT
    it is the description of the service - IOT device

	"""
	type: str = None
	""" type of the IOT device"""


	def __init__(self, iot=None, type=None):
		if iot is not None:
			self.type = iot.type
		else:
			self.type = type 


	def __repr__(self):
		return (f"IoT("
	             "type={self.type})")
	
	def __str__(self):
		return self.__repr__()
	

	def as_cyclonedx(self) -> Component:
		"""Convert IOT to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type DEVICE.
		"""
		properties = [
			Property(name="otupy:type", value="iot")
		]
		if self.type is not None:
			properties.append(Property(name="otupy:iot:type", value=self.type))
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.DEVICE,
			bom_ref=generate_bom_ref("iot"),
			description=self.description,
			properties=properties
		)

