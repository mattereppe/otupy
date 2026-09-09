""" Network firewall

	Defines the main characteristics of an IP firewall.
"""

from otupy.models.ctxd.network_firewall import Firewall

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert Firewall to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="firewall")
	]
	
	rules = self.get('rules')
	if rules is not None:
		properties.append(Property(name="otupy:firewall:rules", value=rules))
	
	return Service(
		name="firewall",
		bom_ref=generate_bom_ref("firewall"),
		properties=properties
	)

Firewall.to_cyclonedx = to_cyclonedx
