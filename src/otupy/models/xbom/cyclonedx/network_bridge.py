""" Network bridge

	Defines the main characteristics of an Ethernet bridge/switch
"""

from otupy.models.ctxd.network_bridge import Bridge

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert Bridge to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="network_bridge")
	]
	
	table = self.get('table')
	if table is not None:
		properties.append(Property(name="otupy:bridge:table", value=table))
	
	ifaces = self.get('ifaces')
	if ifaces is not None:
		properties.append(Property(name="otupy:bridge:iface_count", value=str(len(ifaces))))
		for i, iface in enumerate(ifaces):
			if hasattr(iface, 'to_cyclonedx'):
				iface_props = iface.to_cyclonedx(prefix=f"otupy:bridge:iface:{i}")
				properties.extend(iface_props)
	
	return Service(
		name=table or "network-bridge",
		bom_ref=generate_bom_ref("network_bridge"),
		properties=properties
	)

Bridge.to_cyclonedx = to_cyclonedx
