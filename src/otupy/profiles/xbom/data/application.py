import otupy.types.base
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.profiles.xbom.data.xbom_object import XBOMObject

class Application(XBOMObject):
	""" Application
    	it is the description of the service - software application
	"""
	version: str = None
	""" version of the application """
	owner: str = None
	""" owner of the application """
	app_type: str = None
	""" type of the application """

	def __init__(self, app=None, description = None, id = None, name = None, version = None, owner = None, app_type = None):
		if isinstance(app, Application):
			super().__init__(name=app.name, description=app.description, id=app.id)
			self.version = app.version
			self.owner = app.owner
			self.app_type = app.app_type
		else:	
			super().__init__(name=name, description=description, id=id)
			self.version = version 
			self.owner = owner 
			self.app_type = app_type 


	def getId(self, domain=None, namespace=None):
		return "app:" + str(self.app_type) + "/" + str(domain) + "/" + str(namespace) + "/" + str(self.name) + "@" + str(self.version)
		

	def __repr__(self):
		return (f"Application({super().__repr__()},"
	             f"version='{self.version}', owner={self.owner}, app_type='{self.app_type}')")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Application to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type APPLICATION.
		"""
		properties = [
			Property(name="otupy:type", value="application")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:application:id", value=self.id))
		if self.owner is not None:
			properties.append(Property(name="otupy:application:owner", value=self.owner))
		if self.app_type is not None:
			properties.append(Property(name="otupy:application:type", value=self.app_type))
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.APPLICATION,
			bom_ref=self.getId() if self.id is not None else generate_bom_ref(self),
			version=self.version,
			description=self.description,
			properties=properties
		)
