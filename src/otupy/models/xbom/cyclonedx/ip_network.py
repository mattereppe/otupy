""" Generic IP network

	Defines the main characteristics of a generic IP network.
	This is expected to be used when no information about the concrete implementation of
	the underlying network is available.
"""

from otupy.models.ctxd.ip_network import IPNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert IPNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="ip_network")
	]
	
	nets = self.get('nets')
	if nets is not None:
		for i, net in enumerate(nets):
			net_props = net.to_cyclonedx(prefix=f"otupy:ip_network:{i}")
			properties.extend(net_props)
	
	return Service(
		name="ip-network",
		bom_ref=generate_bom_ref("ip_network"),
		properties=properties
	)

IPNetwork.to_cyclonedx = to_cyclonedx
