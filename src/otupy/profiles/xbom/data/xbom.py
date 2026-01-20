import otupy.types.base

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from cyclonedx.model.service import Service
from cyclonedx.model.dependency import Dependency
from cyclonedx.output.json import JsonV1Dot7
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.schema import SchemaVersion


from otupy.profiles.xbom.data.sbom_format import SbomFormat
from otupy.types.base import Record

from typing import Any
import json

_cyclonedx_schema_version = SchemaVersion.V1_7

class Xbom(Record):
	"""XBOM
	eXtended Bill of Materials
	"""
	format: SbomFormat = None # type: ignore
	""" Format of the XBOM """
    
	bom: Bom = None
	""" CycloneDX Bill of Materials """

	def __init__(self, format: SbomFormat | None = None, bom: Bom = None):
		if format is not None and isinstance(format, Xbom):
			self.format = format.format
			self.bom = format.bom
		else:
			self.format = format if format is not None else SbomFormat.cyclonedx
			self.bom = bom if bom is not None else Bom()

	def add(self, item: Component | Service | Dependency | Any ) -> None:
		""" Add item to the BOM

			:param item: Item to add (Component, Service, or object with as_cyclonedx() method)
			:return: None
		"""
		if self.bom is None:
			self.bom = Bom()

		if isinstance(item, Component):
			self.bom.components.add(item)
			return
		
		if isinstance(item, Service):
			self.bom.services.add(item)
			return

		if hasattr(item, "as_cyclonedx"):
			converted_item = item.as_cyclonedx()
			self.add(converted_item) # Ricorsione per aggiungerlo come Component o Service
			return
		else:
			raise TypeError(f"Cannot add item of type {type(item)} to XBOM. Expected Component, Service, or object with as_cyclonedx() method.")

	def add_dependency(self, ref: Any, depends_on: Component | Service | Any | str) -> None:
		""" Add a dependency to the BOM 

            :param ref: Reference ID of the item that has the dependency. It must be present in the BOM.
            :param depends_on: Item that is depended upon (Component, Service, or object with as_cyclonedx() method, or str for reference ID)
				If a component or a service is provided, it must be already present in the BOM.
            :return: None
        """
		match self.format:
			case SbomFormat.cyclonedx:
				if self.bom is None:
					self.bom = Bom()

				# get the bom_ref of ref
				if isinstance(ref, (Component, Service)):
					ref = ref.bom_ref
				elif hasattr(ref, "as_cyclonedx"):
					converted_ref = ref.as_cyclonedx()
					self.add(converted_ref)
					ref = converted_ref.get_bom_ref()
				elif isinstance(ref, str):
					# assume it's already a reference ID
					pass
				else:
					raise TypeError(f"Cannot add dependency for item of type {type(ref)} to XBOM. Expected Component, Service, object with as_cyclonedx() method, or str for reference ID.")

				if isinstance(depends_on, (Component, Service)):
					if depends_on not in self.bom.components and depends_on not in self.bom.services:
						raise ValueError("The item that is depended upon must be already present in the BOM.")
					depends_on_id = depends_on.bom_ref.value
				elif hasattr(depends_on, "as_cyclonedx"):
					converted_item = depends_on.as_cyclonedx()
					self.add(converted_item)
					depends_on_id = converted_item.get_bom_ref()
				elif isinstance(depends_on, Xbom):
					if depends_on.bom is None:
						raise ValueError("The XBOM provided as dependency has no BOM.")
					# Assuming the XBOM has a single component/service for dependency
					if len(depends_on.bom.components) == 1:
						dep_item = next(iter(depends_on.bom.components))
					elif len(depends_on.bom.services) == 1:
						dep_item = next(iter(depends_on.bom.services))
					else:
						raise ValueError("The XBOM provided as dependency must contain exactly one Component or Service.")
					self.add(dep_item)
					depends_on_id = dep_item.bom_ref.value
				elif isinstance(depends_on, str):
					depends_on_id = depends_on
				else:
					raise TypeError(f"Cannot add dependency on item of type {type(depends_on)} to XBOM. Expected Component, Service, object with as_cyclonedx() method, or str for reference ID.")
				dependency = Dependency(ref=ref, depends_on=[depends_on_id])
				self.bom.dependencies.add(dependency)
			case _:
				raise NotImplementedError(f"Adding dependencies for format {self.format} is not implemented.")


	def merge(self, other: 'Xbom') -> None:
		""" Merge another XBOM into this one

			:param other: Other XBOM to merge
			:return: None
		"""
		if other.bom is None or self.bom is None:
			return

		if self.format != other.format:
			raise ValueError(f"Cannot merge XBOMs with different formats: {self.format} != {other.format}")

		# Merge components
		if other.bom:
			for component in other.bom.components:
				self.bom.components.add(component)

			# Merge services
			for service in other.bom.services:
				self.bom.services.add(service)

			# Merge dependencies
			for dependency in other.bom.dependencies:
				self.bom.dependencies.add(dependency)

	def todict(self, e):
		""" Convert XBOM to dictionary for serialization """
		return {
			'format': e.todict(self.format) if self.format else None,
			'bom': self.serialize() if self.bom else None
		}

	@classmethod
	def fromdict(cls, dic, e):
		""" Create Xbom from dictionary """
		if not isinstance(dic, dict):
			raise TypeError("Expected dictionary")
		
		fmt = dic.get('format')
		if fmt:
			fmt = e.fromdict(SbomFormat, fmt)
		
		instance = cls(format=fmt)
		
		bom_data = dic.get('bom')
		if bom_data:
			instance.deserialize(bom_data)
			
		return instance

	def serialize(self) -> dict:
		""" Serialize the XBOM to a dictionary
		
			:return: Serialized XBOM as a dictionary
		"""
		if self.bom is None:
			return {}

		match self.format:
			case SbomFormat.cyclonedx:
				serializer = JsonV1Dot7(self.bom)
				return json.loads(serializer.output_as_string())
			case _:
				raise NotImplementedError(f"Serialization for format {self.format} is not implemented.")

	def deserialize(self, data: dict | str) -> None:
		""" Deserialize data into the XBOM

			:param data: Data to deserialize
			:return: None
		"""
		match self.format:
			case SbomFormat.cyclonedx:
				validator = JsonStrictValidator(schema_version=_cyclonedx_schema_version)
				data = data if isinstance(data, str) else json.dumps(data)
				if validator.validate_str(data):
					raise ValueError("Invalid CycloneDX JSON data")
				self.bom = Bom.from_json(json.loads(data))
			case _:
				raise NotImplementedError(f"Deserialization for format {self.format} is not implemented.")

	def __repr__(self):
		# return the serialized form for easier debugging
		return f"Xbom(format={self.format}, bom={self.serialize()})"

	def __str__(self):
		if self.bom is None:
			return (f"XBOM(format={self.format}, bom=None)")

		match self.format:
			case SbomFormat.cyclonedx:
				return (f"XBOM("
						f"format={self.format}, "
						f"bom_metadata={self.bom.metadata}, "
						f"components_count={len(self.bom.components)}, "
						f"services_count={len(self.bom.services)})")
			case _:
				return (f"XBOM(format={self.format}, bom=Unknown format)")
