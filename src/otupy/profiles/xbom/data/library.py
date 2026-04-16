from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy import URI
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Library(XBOMObject):
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


	def __repr__(self):
		return (f"Library("
					f"{super().__repr__()},"
	            f"version='{self.version}', source={self.source}, lib_type='{self.lib_type}')")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Library to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type LIBRARY.
		"""
		properties = [
			Property(name="otupy:type", value="library")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:library:id", value=self.id))
		if self.source is not None:
			properties.append(Property(name="otupy:library:source", value=str(self.source)))
		if self.lib_type is not None:
			properties.append(Property(name="otupy:library:type", value=self.lib_type))

		return Component(
			name=self.name or "unknown",
			type=ComponentType.LIBRARY,
			bom_ref=generate_bom_ref("library"),
			version=self.version,
			description=self.description,
			properties=properties
		)
