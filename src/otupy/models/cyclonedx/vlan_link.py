""" Virtual LAN network

	Defines the main characteristics of a VLAN
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class VLANNetwork(Map):
	""" Virtual Local Area Network 

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, vlan_id = str, type = str,
			nets = ArrayOf(IPNetAddress))
	""" Field types
	
		This is the definition of the fields beard by the VLAN network.
		:param name: mnemonic identifier for the network
		:param vlan_id: Identifier for this VLAN segment
		:param type: VLAN protocol (e.g., 802.1Q)
		:param nets: Network addresses used in this network
	"""
	
	def getNets(self):
		nets = []
		if 'type' in self:
			nets.append("type:"+self['type'])
		if 'vlan_id' in self:
			nets.append("vlan:"+self['vlan_id'])
		if 'nets' in self:
			for n in self['nets']:
				nets.append(n)		
		return nets

	def as_cyclonedx(self) -> Service:
		"""Convert VLANNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="vlan_network")
		]
		
		name = self.get('name')
		if name is not None:
			properties.append(Property(name="otupy:vlan:name", value=name))
		
		vlan_id = self.get('vlan_id')
		if vlan_id is not None:
			properties.append(Property(name="otupy:vlan:id", value=vlan_id))
		
		vlan_type = self.get('type')
		if vlan_type is not None:
			properties.append(Property(name="otupy:vlan:type", value=vlan_type))
		
		nets = self.get('nets')
		if nets is not None:
			for i, net in enumerate(nets):
				net_props = net.as_cyclonedx(prefix=f"otupy:vlan:{i}")
				properties.extend(net_props)
		
		return Service(
			name=name or "vlan-network",
			bom_ref=generate_bom_ref("vlan_network"),
			properties=properties
		)
