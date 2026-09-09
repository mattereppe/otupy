from otupy.types.base import Record

class LinuxNetns(Record):
	""" Linux Network Namespace

		A Linux network namespace is a partition of the kernel networking stack, often used to 
		create containers and isolated sandboxes with other namespaces (pid, etc.). 

		According to the very generic definition of ExecutionEnvironment, we consider a network
		namespace as a simple form of environment.

	"""
	inode: str = None
	""" Filesystem inode associated to this namespace """

	def __init__(self, lns = None, inode=None):
		if lns is not None:
			self.inode = lns.inode
		else:
			self.inode = str(inode) if inode is not None else None


	def __repr__(self):
		return (f"LinuxNetns(inode={self.inode})")
	
	def __str__(self):
		return self.__repr__()

from otupy.models.ctxd.linux_ns import LinuxNetns

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert LinuxNS to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type LINUX_NS.
	"""
	properties = [
		Property(name="otupy:type", value="linux_ns")
	]
	if self.inode is not None:
		properties.append(Property(name="otupy:linux_ns:inode", value=self.inode))
	
	# Include nested components from Host
	return Component(
		name="linux_ns",
		type=ComponentType.PLATFORM,
		bom_ref=generate_bom_ref("linux_ns"),
		properties=properties
	)

LinuxNS.to_cyclonedx = to_cyclonedx
