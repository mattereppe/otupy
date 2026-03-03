from otupy.profiles.ctxd.data.ctxd_object import CTXDObject
from otupy import URI

class Package(CTXDObject):
	""" Software package

		This is the model of a software package
	"""
	version: str = None
	""" Version of the application """
	arch: str = None
	""" Platform architecture the package is compiled from """
	source: URI = None
	""" URI to retrieve the package """
	pkg_type: str = None
	""" Type of the package (e.g., rpm, deb) """

	def __init__(self, pkg = None, description = None, id = None, name = None, version = None, arch = None, source = None, pkg_type = None):
		if pkg is not None:
			super().__init__(name=pkg.name, id=pkg.id, description=pkg.description)
			self.version = pkg.version
			self.arch = pkg.arch
			self.source = pkg.owner
			self.pkg_type = pkg.pkg_type
		else:	
			super().__init__(name=name, id=id, description=description)
			self.version = version 
			self.arch = arch
			self.source = source
			self.pkg_type = pkg_type

	def getId(self, domain=None, namespace=None):
		return "pkg:" + str(self.lib_type) + "/" + str(source) + "/" + str(self.name) + "#" + str(self.arch) + "@" + str(self.version)


	def __repr__(self):
		return (f"Application("
					f"{super().__repr__()},"
	            f"version='{self.version}', source={self.source}, arch={self.arch}, app_type='{self.pkg_type}')")
	
	def __str__(self):
		return self.__repr__()

