""" Tunnel link

	Abstract a tun link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf 
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class TunnelNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(server= str, nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param server: The server of the VPN
		:param nets: Network addesses used in this network
	"""
	def getNets(self):
		return self['nets']

	def as_cyclonedx(self) -> Service:
		"""Convert TunnelNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="tunnel_network")
		]
		
		server = self.get('server')
		if server is not None:
			properties.append(Property(name="otupy:tunnel:server", value=server))
		
		nets = self.get('nets')
		if nets is not None:
			for i, net in enumerate(nets):
				net_props = net.as_cyclonedx(prefix=f"otupy:tunnel:{i}")
				properties.extend(net_props)
		
		return Service(
			name=server or "tunnel-network",
			bom_ref=generate_bom_ref("tunnel_network"),
			properties=properties
		)
