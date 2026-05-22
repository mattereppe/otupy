""" Tunnel link

	Abstract a tun link as a sort of point-to-point network	
"""

from otupy.models.ctxd.tunnel_network import TunnelNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert TunnelNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="tunnel_network")
	]
	
	server = self.get('server')
	if server is not None:
		properties.append(Property(name="otupy:tunnel:server", value=server))
	
	nets = self.get('nets')
	if nets is not None:
		for i, net in enumerate(nets):
			net_props = net.to_cyclonedx(prefix=f"otupy:tunnel:{i}")
			properties.extend(net_props)
	
	return Service(
		name=server or "tunnel-network",
		bom_ref=generate_bom_ref("tunnel_network"),
		properties=properties
	)

TunnelNetwork.to_cyclonedx = to_cyclonedx
