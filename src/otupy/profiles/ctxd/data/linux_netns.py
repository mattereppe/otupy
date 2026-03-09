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
