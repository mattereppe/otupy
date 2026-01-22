import otupy.types.base
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref


class OS(otupy.types.base.Record):
	"""OS
    Operating System
	"""
	name: str = None
	""" Name of the OS """
	version: str = None
	""" Version of the OS """
	family: str = None
	""" Family of the OS """
	type: str = None
	""" type of the OS """


	def __init__(self, name = None, version = None, family = None, type = None):
		self.name = str(name) if name is not None else None
		self.version = str(version) if version is not None else None
		self.family = str(family) if family is not None else None
		self.type = str(type) if type is not None else None

	def __repr__(self):
		return (f"OS(name={self.name}, "
	             f"version={self.version}, family={self.family}, type={self.type})")
	
	def __str__(self):
		return f"OS(" \
	            f"name={self.name}, " \
				f"version={self.version}, " \
	            f"family={self.family}, " \
	            f"type={self.type})"

	def as_cyclonedx(self) -> Component:
		"""Convert OS to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type OPERATING_SYSTEM.
		"""
		properties = [
			Property(name="otupy:type", value="os")
		]
		if self.family is not None:
			properties.append(Property(name="otupy:os:family", value=self.family))
		if self.type is not None:
			properties.append(Property(name="otupy:os:type", value=self.type))
		
		return Component(
			name=self.name or "unknown",
			type=ComponentType.OPERATING_SYSTEM,
			bom_ref=generate_bom_ref("os"),
			version=self.version,
			properties=properties
		)

