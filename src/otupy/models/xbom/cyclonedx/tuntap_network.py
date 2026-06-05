""" Tun/Tap link

	Abstract a Tun/Tap application-defined network
"""

from otupy.models.ctxd.tuntap_network import TunTapNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert TunTapNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="tuntap_network")
	]
	
	app = self.get('app')
	if app is not None:
		properties.append(Property(name="otupy:tuntap:app", value=app))
	
	nets = self.get('nets')
	if nets is not None:
		for i, net in enumerate(nets):
			net_props = net.to_cyclonedx(prefix=f"otupy:tuntap:{i}")
			properties.extend(net_props)
	
	return Service(
		name=server or "tuntap-network",
		bom_ref=generate_bom_ref("tuntap_network"),
		properties=properties
	)

TunTapNetwork.to_cyclonedx = to_cyclonedx
