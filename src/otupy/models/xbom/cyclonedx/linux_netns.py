from otupy.models.ctxd.linux_ns import LinuxNetns

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert LinuxNetns to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type LINUX_NS.
	"""
	properties = [
		Property(name="otupy:type", value="linux_netns")
	]
	if self.inode is not None:
		properties.append(Property(name="otupy:linux_netns:inode", value=self.inode))
	
	# Include nested components from Host
	return Component(
		name="linux_netns",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("linux_netns"),
		properties=properties
	)

LinuxNetns.to_cyclonedx = to_cyclonedx
