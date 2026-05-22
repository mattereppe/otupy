""" Network Address Translation

	Defines the main characteristics of a NAT.
"""

from otupy.models.ctxd.network_nat import NAT

from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Service:
	"""Convert NAT to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service representation.
	"""
	properties = [
		Property(name="otupy:type", value="nat")
	]
	
	rules = self.get('rules')
	if rules is not None:
		for i, rule in enumerate(rules):
			properties.append(Property(name=f"otupy:nat:rule:{i}", value=rule))
	
	return Service(
		name="nat",
		bom_ref=generate_bom_ref("nat"),
		properties=properties
	)

NAT.to_cyclonedx = to_cyclonedx
