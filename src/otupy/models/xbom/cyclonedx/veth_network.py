""" Veth pseudo-network

	Abstract a veth link as a sort of point-to-point network	
"""

from otupy.models.ctxd.veth_network import VEthNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert VEthNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="veth_network")
	]
	
	peers = self.get('peers')
	if peers is not None:
		for i, peer in enumerate(peers):
			properties.append(Property(name=f"otupy:veth:peer:{i}", value=str(peer)))
	
	nets = self.get('nets')
	if nets is not None:
		for i, net in enumerate(nets):
			net_props = net.to_cyclonedx(prefix=f"otupy:veth:{i}")
			properties.extend(net_props)
	
	return Service(
		name="veth-network",
		bom_ref=generate_bom_ref("veth_network"),
		properties=properties
	)

VEthNetwork.to_cyclonedx = to_cyclonedx
