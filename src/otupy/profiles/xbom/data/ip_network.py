""" Generic IP network

	Defines the main characteristics of a generic IP network.
	This is expected to be used when no information about the concrete implementation of
	the underlying network is available.
"""

from otupy import Map, ArrayOf
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class IPNetwork(Map):
	""" IP Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the IP network.
	"""

	def as_cyclonedx(self) -> Service:
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
				net_props = net.as_cyclonedx(prefix=f"otupy:ip_network:{i}")
				properties.extend(net_props)
		
		return Service(
			name="ip-network",
			bom_ref=generate_bom_ref("ip_network"),
			properties=properties
		)
