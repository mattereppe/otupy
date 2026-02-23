""" Mobile network

	Defines the main characteristics of a 5G network.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class MobileNetwork(Map):
	""" Mobile 4/5G Network

		A flexible container for network characteristics. 
		Currently expects the network address/prefix as mandatory field.
	"""
	fieldtypes = dict(name = str, mcc = str, mnc = str, region = int, set = int, 
			netv4addrs = ArrayOf(IPv4Net), netv6addrs = ArrayOf(IPv6Net))
	""" Field types
	
		This is the definition of the fields beard by the `Mobile` network.
		:param name: mnemonic identifier for the network
		:param mcc: Mobile Country Code
		:param mnc: Mobile Network Code
		:param region: Region 
		:param set: TBD
		:param netv4addrs: Network addresses used in this network
		:param netv6addrs: Network IPv6 addresses used in this network
	"""

	def as_cyclonedx(self) -> Service:
		"""Convert MobileNetwork to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="mobile_network")
		]
		
		name = self.get('name')
		if name is not None:
			properties.append(Property(name="otupy:mobile:name", value=name))
		
		mcc = self.get('mcc')
		if mcc is not None:
			properties.append(Property(name="otupy:mobile:mcc", value=mcc))
		
		mnc = self.get('mnc')
		if mnc is not None:
			properties.append(Property(name="otupy:mobile:mnc", value=mnc))
		
		region = self.get('region')
		if region is not None:
			properties.append(Property(name="otupy:mobile:region", value=str(region)))
		
		set_val = self.get('set')
		if set_val is not None:
			properties.append(Property(name="otupy:mobile:set", value=str(set_val)))
		
		netv4addrs = self.get('netv4addrs')
		if netv4addrs is not None:
			for i, net in enumerate(netv4addrs):
				properties.append(Property(name=f"otupy:mobile:v4net:{i}", value=str(net)))
		
		netv6addrs = self.get('netv6addrs')
		if netv6addrs is not None:
			for i, net in enumerate(netv6addrs):
				properties.append(Property(name=f"otupy:mobile:v6net:{i}", value=str(net)))
		
		return Service(
			name=name or "mobile-network",
			bom_ref=generate_bom_ref("mobile_network"),
			properties=properties
		)
