""" Veth pseudo-network

	Abstract a veth link as a sort of point-to-point network	
"""

from otupy import Map, ArrayOf , Array
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class VEthPeer(Array):
	""" VEth network interface peers

		A tuple would be more appropriate to store a pair of information
		(interface idx, namespace), but there is not such base type
		in the OpenC2 language. An Array if the most fitting data type.
	"""
	pass

class VEthNetwork(Map):
	""" Virtual Ethernet link

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(peers= ArrayOf(VEthPeer), nets = ArrayOf(IPNetAddress))

	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param peers: A couple of interfaces names
		:param nets: Network addesses used in this network
	"""
	
	def getNets(self):
		return self['nets']

	def as_cyclonedx(self) -> Service:
		"""Convert VEthNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="veth_network")
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
			name="veth-network",
			bom_ref=generate_bom_ref("veth_network"),
			properties=properties
		)
