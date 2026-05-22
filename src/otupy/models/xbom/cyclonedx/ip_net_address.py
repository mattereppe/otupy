from otupy.models.ctxd.ip_net_address import IPNetAddress

from cyclonedx.model import Property

def to_cyclonedx(self, prefix: str = "otupy:net") -> list:
	"""Convert IPNetAddress to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		list: List of CycloneDX Property objects.
	"""
	properties = [
		Property(name=f"{prefix}:address", value=str(self.getObj()))
	]
	return properties

IPNetAddress.to_cyclonedx = to_cyclonedx
