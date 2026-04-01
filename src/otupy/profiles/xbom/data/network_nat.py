""" Network Address Translation

	Defines the main characteristics of a NAT.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class NAT(Map):
	""" NAT

		A flexible container for NAT configurations.
		To be implemented
	"""
	fieldtypes = dict(rules= ArrayOf(str))
	""" Field types
	
		This is the definition of the translation table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"NAT({self['rules'] if 'rules' in self else None})"

	def as_cyclonedx(self) -> Service:
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
