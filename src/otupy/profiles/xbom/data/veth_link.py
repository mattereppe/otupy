""" Veth pseudo-network

	Abstract a veth link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf 
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class VEthNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(peers= tuple, nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param peers: A couple of interfaces names
		:param namespaces: A couple of namespaces which the peers belong to (same order)
		:param nets: Network addesses used in this network
	"""

	def as_cyclonedx(self) -> Service:
		"""Convert VEthNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="veth_link")
		]
		
		peers = self.get('peers')
		if peers is not None:
			for i, peer in enumerate(peers):
				properties.append(Property(name=f"otupy:veth:peer:{i}", value=str(peer)))
		
		nets = self.get('nets')
		if nets is not None:
			for i, net in enumerate(nets):
				net_props = net.as_cyclonedx(prefix=f"otupy:veth:{i}")
				properties.extend(net_props)
		
		return Service(
			name="veth-link",
			bom_ref=generate_bom_ref("veth_link"),
			properties=properties
		)
