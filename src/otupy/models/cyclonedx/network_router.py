""" Network router

	Defines the main characteristics of an IP router.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Router(Map):
	""" Router

		A flexible container for routing configurations.
		To be implemented
	"""
	fieldtypes = dict(routes= str)
	""" Field types
	
		This is the definition of the routing table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"Router({self['routes'] if 'routes' in self else None})"

	def as_cyclonedx(self) -> Service:
		"""Convert Router to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="router")
		]
		
		routes = self.get('routes')
		if routes is not None:
			properties.append(Property(name="otupy:router:routes", value=routes))
		
		return Service(
			name="router",
			bom_ref=generate_bom_ref("router"),
			properties=properties
		)
