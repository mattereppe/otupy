""" Virtual eXtended LAN network

	Defines the main characteristics of a VXLAN
"""

from otupy.models.ctxd.vxlan_network import VXLANNetwork

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert VXLANNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="vxlan_network")
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
			net_props = net.to_cyclonedx(prefix=f"otupy:vxlan:{i}")
			properties.extend(net_props)
	
	return Service(
		name=vni or "vxlan-network",
		bom_ref=generate_bom_ref("vxlan_network"),
		properties=properties
	)

VXLANNetwork.to_cyclonedx = to_cyclonedx
