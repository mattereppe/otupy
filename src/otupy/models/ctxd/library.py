from otupy.models.ctxd.ctxd_object import CTXDObject
from otupy import URI

class Library(CTXDObject):
	""" Software library

		This is the model of a software library
	"""
	version: str = None
	""" Version of the library """
	source: URI = None
	""" URI to retrieve the library """
	lib_type: str = None
	""" Type of the library (e.g., runtime, headerfiles) """

	def __init__(self, lib = None, description = None, id = None, name = None, version = None, source = None, lib_type = None):
		if lib is not None:
			super().__init__(name=lib.name, id=lib.id, description=lib.description)
			self.version = lib.version
			self.source = lib.source
			self.lib_type = lib.lib_type
		else:	
			super().__init__(name=name, id=id, description=description)
			self.version = version 
			self.source = source
			self.lib_type = lib_type

	def getId(self, domain=None, namespace=None):
		return "lib:" + str(self.lib_type) + "/" + str(source) + "/" + str(self.name) + "@" + str(self.version)

	def __repr__(self):
		return (f"Library("
					f"{super().__repr__()},"
	            f"version='{self.version}', source={self.source}, lib_type='{self.lib_type}')")
	
	def __str__(self):
		return self.__repr__()

