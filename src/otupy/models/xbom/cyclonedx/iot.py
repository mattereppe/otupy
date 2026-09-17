from otupy.models.ctxd.iot import IoT

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
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
		name="iot-device",
		type=ComponentType.DEVICE,
		bom_ref=generate_bom_ref("iot"),
		properties=properties
	)

IoT.to_cyclonedx = to_cyclonedx
