from otupy.models.ctxd.network_interface import IPAddress, IPInfo, NetworkInterface

from otupy.core.extensions import Register
from cyclonedx.model import Property
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def ipinfotocyclonedx(self, prefix: str = "otupy:ipinfo") -> list:
	"""Convert IPInfo to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		list: List of CycloneDX Property objects.
	"""
	properties = [
		Property(name=f"{prefix}:ip", value=str(self.ip)),
		Property(name=f"{prefix}:prefix", value=str(self.prefix))
	]
	if self.gw is not None:
		properties.append(Property(name=f"{prefix}:gateway", value=str(self.gw)))
	return properties

IPInfo.to_cyclonedx = ipinfotocyclonedx

def to_cyclonedx(self, prefix: str = "otupy:iface") -> list:
	"""Convert NetworkInterface to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		list: List of CycloneDX Property objects.
	"""
	properties = []
	
	iface_id = self.id if self.id is not None else "0"
	properties.append(Property(name=f"{prefix}:id", value=iface_id))
	
	if self.description is not None:
		properties.append(Property(name=f"{prefix}:{iface_id}:description", value=self.description))
	if self.iface is not None:
		properties.append(Property(name=f"{prefix}:{iface_id}:name", value=self.iface))
	if self.mac is not None:
		properties.append(Property(name=f"{prefix}:{iface_id}:mac", value=str(self.mac)))
	if self.ips is not None:
		for i, ip_info in enumerate(self.ips):
			ip_props = ip_info.to_cyclonedx(prefix=f"{prefix}:{iface_id}:ip:{i}")
			properties.extend(ip_props)
	
	return properties

NetworkInterface.to_cyclonedx = to_cyclonedx
