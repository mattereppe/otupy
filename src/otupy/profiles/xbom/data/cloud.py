from otupy.profiles.xbom.data.xbom_object import XBOMObject
import otupy.types.base
from cyclonedx.model import Property
from cyclonedx.model.contact import OrganizationalEntity
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class Cloud(XBOMObject):
	"""Cloud
    it is the description of the service - Cloud
	"""
	type: str = None
	""" type of the cloud service"""

	def __init__(self, cloud = None, description = None, id = None, name = None, type = None):
		if isinstance(cloud, Cloud):
			super().__init__(name=cloud.name, description=cloud.description, id=cloud.id)
			self.type = cloud.type
		else:
			super().__init__(name=name, description=description, id=id)
			self.type = type 

	def get_subtype(self):
		""" This function might be replace in the future by
			providing type classes like for other services."""
		return self.type

	def __repr__(self):
		return (f"Cloud(description={self.description}, id={self.id}, "
	             f"name={self.name}, type={self.type})")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Service:
		"""Convert Cloud to CycloneDX service format.
		
		Returns:
			Service: CycloneDX Service representation.
		"""
		properties = [
			Property(name="otupy:type", value="cloud")
		]
		if self.type is not None:
			properties.append(Property(name="otupy:cloud:type", value=self.get_subtype() if hasattr(self, 'get_subtype') else str(self.type)))
		if self.id is not None:
			properties.append(Property(name="otupy:cloud:id", value=self.id))
		
		provider = OrganizationalEntity(name=self.name) if self.name else None
		
		return Service(
			name=self.name or "unknown",
			bom_ref=generate_bom_ref("cloud"),
			description=self.description,
			provider=provider,
			properties=properties
		)
