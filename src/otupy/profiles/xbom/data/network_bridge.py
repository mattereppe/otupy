""" Network bridge

	Defines the main characteristics of an Ethernet bridge/switch
"""

from otupy import Map, ArrayOf
from otupy.profiles.xbom.data.network_interface import NetworkInterface
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Bridge(Map):
	""" Bridge

		A flexible container for network switches/bridges.
		To be implemented
	"""
	fieldtypes = dict(table= str, ifaces=ArrayOf(NetworkInterface) )
	""" Field types
	
		This is the definition of the bridge switching table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"Bridge({self['table'] if 'table' in self else None})"

	def as_cyclonedx(self) -> Service:
		"""Convert Bridge to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="network_bridge")
		]
		
		table = self.get('table')
		if table is not None:
			properties.append(Property(name="otupy:bridge:table", value=table))
		
		ifaces = self.get('ifaces')
		if ifaces is not None:
			properties.append(Property(name="otupy:bridge:iface_count", value=str(len(ifaces))))
			for i, iface in enumerate(ifaces):
				if hasattr(iface, 'as_cyclonedx'):
					iface_props = iface.as_cyclonedx(prefix=f"otupy:bridge:iface:{i}")
					properties.extend(iface_props)
		
		return Service(
			name=table or "network-bridge",
			bom_ref=generate_bom_ref("network_bridge"),
			properties=properties
		)
