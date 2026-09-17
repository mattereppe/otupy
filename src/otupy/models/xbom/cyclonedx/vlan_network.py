""" Virtual LAN network

	Defines the main characteristics of a VLAN
"""

from otupy.models.ctxd.vlan_network import VLANNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert VLANNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="vlan_network")
	]
	
	vni = self.get('vni')
	if vni is not None:
		properties.append(Property(name="otupy:vxlan:vni", value=vni))
	
	port = self.get('port')
	if port is not None:
		properties.append(Property(name="otupy:vxlan:port", value=port))
	
	nets = self.get('nets')
	if nets is not None:
		for i, net in enumerate(nets):
			net_props = net.to_cyclonedx(prefix=f"otupy:vlan:{i}")
			properties.extend(net_props)
	
	return Service(
		name=name or "vlan-network",
		bom_ref=generate_bom_ref("vlan_network"),
		properties=properties
	)

VLANNetwork.to_cyclonedx = to_cyclonedx
