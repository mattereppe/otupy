""" Virtual LAN network

	Defines the main characteristics of a  VLAN
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

from otupy.models.ctxd.ip_net_address import IPNetAddress


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


