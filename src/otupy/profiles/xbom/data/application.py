import otupy.types.base
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType

class Application(otupy.types.base.Record):
	"""Application
    it is the description of the service - software application
	"""
	description: str = None
	""" Generic description of the application """
	id: str = None
	""" Unique local identifier of the application """
	name: str = None
	""" name of the application """
	version: str = None
	""" version of the application """
	owner: str = None
	""" owner of the application """
	app_type: str = None
	""" type of the application """

	def __init__(self, description = None, id = None, name = None, version = None, owner = None, app_type = None):
		if isinstance(description, Application):
			self.description = description.description
			self.id = description.id
			self.name = description.name
			self.version = description.version
			self.owner = description.owner
			self.app_type = description.app_type
		else:	
			self.description = description if description is not None else None
			self.id = id if id is not None else None
			self.name = name if name is not None else None
			self.version = version if version is not None else None
			self.owner = owner if owner is not None else None
			self.app_type = app_type if app_type is not None else None
		self.validate_fields()


	def __repr__(self):
		return (f"Application(description='{self.description}', name={self.name}, "
	             f"version='{self.version}', owner={self.owner}, app_type='{self.app_type}')")
	
	def __str__(self):
		return f"Application(" \
	            f"description={self.description}, " \
	            f"name={self.name}, " \
	            f"version={self.version}, " \
	            f"owner={self.owner}, " \
	            f"app_type={self.app_type})"


	def validate_fields(self):
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type {str}, but got {type(self.id)}")
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type {str}, but got {type(self.name)}")
		if self.version is not None and not isinstance(self.version, str):
			raise TypeError(f"Expected 'version' to be of type {str}, but got {type(self.version)}")
		if self.owner is not None and not isinstance(self.owner, str):
			raise TypeError(f"Expected 'owner' to be of type {str}, but got {type(self.owner)}")
		if self.app_type is not None and not isinstance(self.app_type, str):
			raise TypeError(f"Expected 'app_type' to be of type {str}, but got {type(self.app_type)}")

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
			version=self.version,
			description=self.description,
			properties=properties
		)
