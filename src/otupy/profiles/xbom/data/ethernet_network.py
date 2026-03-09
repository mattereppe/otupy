""" Ethernet network

	Defines the main characteristics of an Ethernet network.
	Includes both virtual and physical infrastructures.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net 
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class EthernetNetwork(Map):
	""" Ethernet Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(nets = ArrayOf(IPNetAddress), netv4nets = ArrayOf(IPv4Net), netv6nets = ArrayOf(IPv6Net))
	""" Field types
	
		This is the definition of the fields beard by the `Ethernet` network.
	"""
	def getNets(self):
		return self['nets']

	def as_cyclonedx(self) -> Service:
		"""Convert EthernetNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="ethernet_network")
		]
		
		nets = self.get('nets')
		if nets is not None:
			for i, net in enumerate(nets):
				net_props = net.as_cyclonedx(prefix=f"otupy:ethernet:{i}")
				properties.extend(net_props)
		
		netv4nets = self.get('netv4nets')
		if netv4nets is not None:
			for i, net in enumerate(netv4nets):
				properties.append(Property(name=f"otupy:ethernet:v4net:{i}", value=str(net)))
		
		netv6nets = self.get('netv6nets')
		if netv6nets is not None:
			for i, net in enumerate(netv6nets):
				properties.append(Property(name=f"otupy:ethernet:v6net:{i}", value=str(net)))
		
		return Service(
			name="ethernet-network",
			bom_ref=generate_bom_ref("ethernet_network"),
			properties=properties
		)
