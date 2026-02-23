from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy import URI
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref

class Package(XBOMObject):
	""" Software package

		This is the model of a software package
	"""
	version: str = None
	""" Version of the package """
	source: URI = None
	""" URI to retrieve the package """
	pkg_type: str = None
	""" Type of the package (e.g., rpm, deb) """

	def __init__(self, pkg = None, description = None, id = None, name = None, version = None, source = None, pkg_type = None):
		if pkg is not None:
			super().__init__(name=pkg.name, id=pkg.id, description=pkg.description)
			self.version = pkg.version
			self.source = pkg.source
			self.pkg_type = pkg.pkg_type
		else:	
			super().__init__(name=name, id=id, description=description)
			self.version = version 
			self.source = source
			self.pkg_type = pkg_type


	def __repr__(self):
		return (f"Package("
					f"{super().__repr__()},"
	            f"version='{self.version}', source={self.source}, pkg_type='{self.pkg_type}')")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Package to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type LIBRARY (CycloneDX uses LIBRARY for packages).
		"""
		properties = [
			Property(name="otupy:type", value="package")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:package:id", value=self.id))
		if self.source is not None:
			properties.append(Property(name="otupy:package:source", value=str(self.source)))
		if self.pkg_type is not None:
			properties.append(Property(name="otupy:package:type", value=self.pkg_type))

		return Component(
			name=self.name or "unknown",
			type=ComponentType.LIBRARY,
			bom_ref=generate_bom_ref("package"),
			version=self.version,
			description=self.description,
			properties=properties
		)
