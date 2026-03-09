import otupy.types.base
from otupy.profiles.xbom.data.abstract_xbom import Xbom

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from cyclonedx.model.service import Service
from cyclonedx.model.dependency import Dependency
from cyclonedx.model import ExternalReference, ExternalReferenceType
from cyclonedx.output.json import JsonV1Dot7
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.schema import SchemaVersion
from cyclonedx.model import Property
from cyclonedx.model.bom_ref import BomRef

import uuid
from otupy.types.base import Record

from typing import Any, List
import json

from otupy.profiles.xbom.data.xbom_format import XbomFormat

_cyclonedx_schema_version = SchemaVersion.V1_7

class CyclonedxXbom(Xbom):
	"""CycloneDX implementation of XBOM
	
	eXtended Bill of Materials using CycloneDX format.
	This is the concrete implementation that uses the CycloneDX library.
	"""
	format: XbomFormat = None # type: ignore
	""" Format of the XBOM """
    
	bom: Bom = None
	""" CycloneDX Bill of Materials """

	def __init__(self, format: XbomFormat | None = None, bom: Bom = None):
		if format is not None and isinstance(format, Xbom):
			self.format = format.format
			self.bom = format.bom
		else:
			self.format = format if format is not None else XbomFormat.cyclonedx
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

		if isinstance(item, list):
			for p in item:
				if isinstance(p, Property):
					self.add(p)
			return

		if hasattr(item, "as_cyclonedx"):
			converted_item = item.as_cyclonedx()
			self.add(converted_item) # Ricorsione per aggiungerlo come Component o Service
			return
		else:
			raise TypeError(f"Cannot add item of type {type(item)} to XBOM. Expected Component, Service, or object with as_cyclonedx() method.")

	def get_bom_serial_number(self) -> str:
		""" Get or create the BOM's serial number (UUID)
		
			CycloneDX BOMs have a serial number that uniquely identifies the BOM.
			If not set, a new UUID will be generated and assigned.
		
			:return: The serial number as a UUID string (without 'urn:uuid:' prefix)
		"""
		if self.bom is None:
			self.bom = Bom()
		
		if self.bom.serial_number is None:
			# serialize it to force UUID generation
			self.serialize()
			if self.bom.serial_number is None: # just in case
				self.bom.serial_number = f"urn:uuid:{uuid.uuid4()}"
		
		# Return just the UUID part (serial_number is already a UUID object)
		return str(self.bom.serial_number)

	def get_bom_version(self) -> int:
		""" Get the BOM's version number
		
			:return: The version number (defaults to 1 if not set)
		"""
		if self.bom is None:
			return 1
		return self.bom.version if self.bom.version else 1

	def get_bom_link(self, element_bom_ref: str) -> str:
		""" Generate a CycloneDX bom-link URI for an element in this BOM
		
			Bom-link format: urn:cdx:{serial-number}/{version}#{bom-ref}
			See: https://cyclonedx.org/capabilities/bomlink/
		
			:param element_bom_ref: The bom-ref of the element.
			:return: A properly formatted bom-link URI
		"""
		serial_number = self.get_bom_serial_number()
		version = self.get_bom_version()
		
		if element_bom_ref is None:
			raise ValueError("Cannot create bom-link without a bom_ref")
		
		return f"urn:cdx:{serial_number}/{version}#{element_bom_ref}"

	def add_external_reference(self, target_ref: str, url: str, ref_type: ExternalReferenceType = ExternalReferenceType.BOM, 
							   comment: str | None = None) -> None:
		""" Add an external reference to a specific component or service in this XBOM
		
			External references are used to link to other BOMs that contain related components.
		
			:param target_ref: The bom_ref of the component/service to add the reference to
			:param url: URL or URI of the external reference
			:param ref_type: Type of external reference (default: BOM)
			:param comment: Optional comment describing the external reference
			:return: None
		"""
		if self.bom is None:
			raise ValueError("Cannot add external reference to an empty BOM")
		
		# Find the item by bom_ref
		target_item = None
		for comp in self.bom.components:
			if comp.bom_ref and comp.bom_ref.value == target_ref:
				target_item = comp
				break
		if target_item is None:
			for svc in self.bom.services:
				if svc.bom_ref and svc.bom_ref.value == target_ref:
					target_item = svc
					break
		if target_item is None:
			raise ValueError(f"No component or service with bom_ref '{target_ref}' found")
		
		ext_ref = ExternalReference(
			type=ref_type,
			url=url,
			comment=comment
		)
		
		if target_item.external_references is None:
			target_item.external_references = []
		target_item.external_references.add(ext_ref)

	def find_ref_by_name(self, name: str) -> str | None:
		""" Find the bom_ref of a component or service by name

			:param name: The name to search for
			:return: The bom_ref string if found, None otherwise
		"""
		if self.bom is None:
			return None
		for service in self.bom.services:
			if service.name == name:
				return service.bom_ref.value if service.bom_ref else None
		for component in self.bom.components:
			if component.name == name:
				return component.bom_ref.value if component.bom_ref else None
		return None

	def add_dependency(self, parent_ref: str, child_ref: str) -> None:
		""" Add a dependency relationship

			Creates a dependency where child_ref depends on parent_ref.

			:param parent_ref: The bom_ref of the item that is depended upon
			:param child_ref: The bom_ref of the dependent item
			:return: None
		"""
		if self.bom is None:
			raise ValueError("Cannot add dependency to an empty BOM")
		if not parent_ref or not child_ref:
			raise ValueError("Both parent_ref and child_ref must be provided")
		# check that both refs exist in the BOM
		parent_exists = any((comp.bom_ref and comp.bom_ref.value == parent_ref) for comp in self.bom.components) or \
						any((svc.bom_ref and svc.bom_ref.value == parent_ref) for svc in self.bom.services)
		child_exists = any((comp.bom_ref and comp.bom_ref.value == child_ref) for comp in self.bom.components) or \
					   any((svc.bom_ref and svc.bom_ref.value == child_ref) for svc in self.bom.services)
		if not parent_exists:
			raise ValueError(f"parent_ref '{parent_ref}' does not exist in the BOM")
		if not child_exists:
			raise ValueError(f"child_ref '{child_ref}' does not exist in the BOM")

		dependency = Dependency(ref=BomRef(child_ref), dependencies=[Dependency(ref=BomRef(parent_ref))])
		self.bom.dependencies.add(dependency)

	def add_dependency_with_external_ref(self, depends_on_xbom: 'Xbom', from_ref: str, comment: str | None = None) -> None:
		""" Add both an external reference and a dependency to another XBOM
		
			This is a convenience method that adds the dependency XBOM as an external reference
			and creates a dependency relationship.
			
			The external reference uses the CycloneDX bom-link format:
			urn:cdx:{serial-number}/{version}#{bom-ref}
			See: https://cyclonedx.org/capabilities/bomlink/
		
			:param depends_on_xbom: The XBOM that this XBOM depends on
			:param from_ref: The bom_ref of the item in this BOM that depends on the other
			:param comment: Optional comment describing the dependency
			:return: None
		"""
		dep_ref = depends_on_xbom.find_ref_by_name  # we need to get a ref from the other bom
		# Get the first ref from the other BOM's components or services
		dep_bom_ref = None
		if depends_on_xbom.bom is not None:
			for comp in depends_on_xbom.bom.components:
				if comp.bom_ref:
					dep_bom_ref = comp.bom_ref.value
					break
			if dep_bom_ref is None:
				for svc in depends_on_xbom.bom.services:
					if svc.bom_ref:
						dep_bom_ref = svc.bom_ref.value
						break
		if dep_bom_ref is None:
			raise ValueError("The dependency XBOM must have at least one item with a bom_ref")
		
		# Generate a proper CycloneDX bom-link URL
		bom_link = depends_on_xbom.get_bom_link(dep_bom_ref)
		
		# Add external reference pointing to the dependency BOM using bom-link format
		self.add_external_reference(
			target_ref=from_ref,
			url=bom_link,
			ref_type=ExternalReferenceType.BOM,
			comment=comment
		)
		
		# Add the dependency relationship
		self.add_dependency(dep_bom_ref, from_ref)

	def add_link(self, item_ref: str, link: any) -> None:
		""" Add a link to an item in the BOM by bom_ref
		
			This is a convenience method that finds the bom_ref of the item by name and adds it as a property.
		
			:param item_name: The name of the item to link to
			:return: None
		"""
		if self.bom is None:
			raise ValueError("Cannot add link to an empty BOM")
		
		link = link.as_cyclonedx() if hasattr(link, 'as_cyclonedx') else link

		# Look up for the right item to add the link to
		for service in self.bom.services:
			if service.bom_ref and service.bom_ref.value == item_ref:
				if isinstance(link, list):
					for prop in link:
						service.properties.add(prop)
				else:
					service.properties.add(link)
				return
		for component in self.bom.components:
			if component.bom_ref and component.bom_ref.value == item_ref:
				if isinstance(link, list):
					for prop in link:
						component.properties.add(prop)
				else:
					component.properties.add(link)
				return

		raise ValueError(f"No component or service with bom_ref '{item_ref}' found in the BOM")

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
		
		# print(f"DEBUG fromdict - Input dic keys: {dic.keys()}")
		# print(f"DEBUG fromdict - Full dic: {dic}")
		
		fmt = dic.get('format')
		if fmt:
			if isinstance(fmt, XbomFormat):
				pass  # already the correct type
			elif isinstance(fmt, dict):
				fmt = e.fromdict(fmt)
			else:
				fmt = XbomFormat[str(fmt)]  # convert string/int name to enum
		else:
			fmt = XbomFormat.cyclonedx  # Default format
		
		instance = cls(format=fmt)
		
		bom_data = dic.get('bom')
		# print(f"DEBUG fromdict - bom_data type: {type(bom_data)}")
		# print(f"DEBUG fromdict - bom_data: {bom_data}")
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
			case XbomFormat.cyclonedx:
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
			case XbomFormat.cyclonedx:
				validator = JsonStrictValidator(schema_version=_cyclonedx_schema_version)
				data = data if isinstance(data, str) else json.dumps(data)
				validation_result = validator.validate_str(data)
				if validator.validate_str(data):
					raise ValueError("Invalid CycloneDX JSON data")
				self.bom = Bom.from_json(json.loads(data))
			case _:
				raise NotImplementedError(f"Deserialization for format {self.format} is not implemented.")

	def __repr__(self):
		return f"Xbom(format={self.format}, bom=({len(self.bom.services)} services, {len(self.bom.components)} components))"

	def __str__(self):
		if self.bom is None:
			return (f"XBOM(format={self.format}, bom=None)")

		match self.format:
			case XbomFormat.cyclonedx:
				return (f"XBOM("
						f"format={self.format}, "
						f"bom_metadata={self.bom.metadata}, "
						f"components_count={len(self.bom.components)}, "
						f"services_count={len(self.bom.services)})")
			case _:
				return (f"XBOM(format={self.format}, bom=Unknown format)")
