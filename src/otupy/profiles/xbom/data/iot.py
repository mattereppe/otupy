from otupy.profiles.xbom.data.host import Host
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class IOT(Host):
	"""IOT
    it is the description of the service - IOT device

	"""
	type: str = None
	""" type of the IOT device"""


	def __init__(self, iot=None, type=None, **kwargs):
		if isinstance(iot, IOT):
			super().__init__(iot)
			self.type = iot.type
		else:
			super().__init__(**kwargs)
			self.type = type 

	def __repr__(self):
		return (f"IoT("
					 f"{super().__repr__()},"
	             f"type={self.type})")
	
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
		if self.id is not None:
			properties.append(Property(name="otupy:iot:id", value=self.id))
		if self.type is not None:
			properties.append(Property(name="otupy:iot:device-type", value=self.type))
		if self.vendor is not None:
			properties.append(Property(name="otupy:iot:vendor", value=self.vendor))
		if self.model is not None:
			properties.append(Property(name="otupy:iot:model", value=self.model))
		if self.serial is not None:
			properties.append(Property(name="otupy:iot:serial", value=self.serial))
		if self.firmware is not None:
			properties.append(Property(name="otupy:iot:firmware", value=self.firmware))
		if self.version is not None:
			properties.append(Property(name="otupy:iot:version", value=self.version))
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.DEVICE,
			bom_ref=generate_bom_ref("iot"),
			description=self.description,
			properties=properties
		)

