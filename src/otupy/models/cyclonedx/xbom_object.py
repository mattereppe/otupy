from otupy.types.base import Record
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class XBOMObject(Record):
	""" Common fields to all XBOM model objects """

	name: str = None
	""" A name for this node (e.g., network namespace name) """
	id: str = None
	""" ID of the node, preferably globally unique """
	description: str = None
	""" Generic description of the node (including its role) """

	def __init__(self, 
			name:str = None,
			id:str = None, 
			description:str = None): 
		self.name = str(name) if name is not None else None
		self.id = id if id is not None else None
		self.description = description if description is not None else None

	def __repr__(self):
		return (
				f"name='{self.name}',"
				f"id={self.id}, "
				f"description='{self.description}'," 
			)
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert XBOMObject to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		properties = [
			Property(name="otupy:type", value="xbom_object")
		]
		if self.id is not None:
			properties.append(Property(name="otupy:xbom_object:id", value=self.id))

		return Component(
			name=self.name or "unknown",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("xbom_object"),
			description=self.description,
			properties=properties
		)
