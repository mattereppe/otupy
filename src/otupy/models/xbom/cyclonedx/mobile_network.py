""" Mobile network

	Defines the main characteristics of a 5G network.
"""

from otupy.models.ctxd.mobile_network import MobileNetwork 

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress

def to_cyclonedx(self) -> Service:
	"""Convert MobileNetwork to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="mobile_network")
	]
	
	name = self.get('name')
	
	mcc = self.get('mcc')
	if mcc is not None:
		properties.append(Property(name="otupy:mobile:mcc", value=mcc))
	
	mnc = self.get('mnc')
	if mnc is not None:
		properties.append(Property(name="otupy:mobile:mnc", value=mnc))
	
	region = self.get('region')
	if region is not None:
		properties.append(Property(name="otupy:mobile:region", value=str(region)))
	
	sst_val = self.get('sst')
	if sst_val is not None:
		properties.append(Property(name="otupy:mobile:sst", value=str(sst_val)))
	
	netaddrs = self.get('nets')
	if netaddrs is not None:
		for i, net in enumerate(netaddrs):
			properties.append(Property(name=f"otupy:mobile:ipnet:{i}", value=str(net)))
	

	
	return Service(
		name=name or "mobile-network",
		bom_ref=generate_bom_ref("mobile_network"),
		properties=properties
	)

MobileNetwork.to_cyclonedx = to_cyclonedx
