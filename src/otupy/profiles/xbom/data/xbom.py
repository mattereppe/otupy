from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component
from cyclonedx.model.service import Service
from cyclonedx.model.dependency import Dependency
from cyclonedx.model import ExternalReference, ExternalReferenceType, XsUri
from cyclonedx.output.json import JsonV1Dot7
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.schema import SchemaVersion
from cyclonedx.model import Property
from cyclonedx.model.bom_ref import BomRef

from otupy.profiles.xbom.data.sbom_format import SbomFormat
from otupy.profiles.xbom.data.abstract_xbom import Xbom, _XBOM_FORMAT_REGISTRY
from otupy.profiles.xbom.data.bom_ref import generate_uuid

from typing import Any, cast
from uuid import UUID
import json

_cyclonedx_schema_version = SchemaVersion.V1_7


class CyclonedxXbom(Xbom):
	"""CycloneDX implementation of XBOM
	
	eXtended Bill of Materials using CycloneDX format.
	This is the concrete implementation that uses the CycloneDX library.
	"""
    
	bom: Bom | None = None
	""" CycloneDX Bill of Materials """

	def __init__(self, format: SbomFormat | None = None, bom: Bom | None = None):
		if format is not None and isinstance(format, CyclonedxXbom):
			self.format = format.format
			self.bom = format.bom
		else:
			self.format = format if format is not None else SbomFormat.cyclonedx
			self.bom = bom if bom is not None else Bom()

	def _ensure_bom(self) -> Any:
		""" Ensure bom is initialized and return it with proper type.
		
			Note: Returns Any to work around cyclonedx library type union issues.
			The actual return value is always a Bom instance.
		
			:return: The Bom instance
		"""
		if self.bom is None:
			self.bom = Bom()
		return self.bom

	def add(self, item: Component | Service | Dependency | Any ) -> None:
		""" Add item to the BOM

			:param item: Item to add (Component, Service, or object with as_cyclonedx() method)
			:return: None
		"""
		bom = self._ensure_bom()

		if isinstance(item, Component):
			bom.components.add(item)
			return
		
		if isinstance(item, Service):
			bom.services.add(item)
			return

		if isinstance(item, Property) or isinstance(item, list) and all(isinstance(p, Property) for p in item):
			if len(bom.components) == 1:
				target_props = next(iter(bom.components)).properties
			elif len(bom.services) == 1:
				target_props = next(iter(bom.services)).properties
			else:
				raise ValueError("XBOM must contain exactly one Component or Service to add a Property.")

			if isinstance(item, list):
				target_props.update(item)
			else:
				target_props.add(item)
			return

		if isinstance(item, list):
			for p in item:
				if isinstance(p, Property):
					self.add(p)
			return

		if hasattr(item, "as_cyclonedx"):
			converted_item = cast(Any, item).as_cyclonedx()
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
		bom = self._ensure_bom()
		
		if bom.serial_number is None:
			bom.serial_number = UUID(generate_uuid())
		
		return str(bom.serial_number)

	def get_bom_version(self) -> int:
		""" Get the BOM's version number
		
			:return: The version number (defaults to 1 if not set)
		"""
		if self.bom is None:
			return 1
		bom = self._ensure_bom()
		return bom.version if bom.version else 1

	def get_bom_link(self, element_bom_ref: str | None = None) -> str:
		""" Generate a CycloneDX bom-link URI for an element in this BOM
		
			Bom-link format: urn:cdx:{serial-number}/{version}#{bom-ref}
			See: https://cyclonedx.org/capabilities/bomlink/
		
			:param element_bom_ref: The bom-ref of the element. If None, uses the main item's bom_ref.
			:return: A properly formatted bom-link URI
		"""
		serial_number = self.get_bom_serial_number()
		version = self.get_bom_version()
		
		if element_bom_ref is None:
			element_bom_ref = self.get_bom_ref()
		
		if element_bom_ref is None:
			raise ValueError("Cannot create bom-link without a bom_ref")
		
		return f"urn:cdx:{serial_number}/{version}#{element_bom_ref}"

	def get_bom_ref(self) -> str | None:
		""" Get the bom_ref of the main component or service in this XBOM
		
			:return: The bom_ref value if available, None otherwise
		"""
		if self.bom is None:
			return None
		
		main_item = self.get_main_item()
		if main_item is not None:
			main = cast(Any, main_item)
			if main.bom_ref is not None:
				return main.bom_ref.value
		return None

	def get_main_item(self) -> Component | Service | None:
		""" Get the main component or service in this XBOM
		
			Ignores stub components/services that have external references (used to represent
			external dependencies).
		
			:return: The main Component or Service if there is exactly one, None otherwise
		"""
		if self.bom is None:
			return None
		bom = self._ensure_bom()
		
		def is_stub(item: Any) -> bool:
			if item.external_references:
				for ref in item.external_references:
					if ref.type == ExternalReferenceType.BOM:
						return True
			return False
		
		main_components = [c for c in bom.components if not is_stub(c)]
		main_services = [s for s in bom.services if not is_stub(s)]
		
		if len(main_components) == 1 and len(main_services) == 0:
			return main_components[0]
		elif len(main_services) == 1 and len(main_components) == 0:
			return main_services[0]
		return None

	def add_external_reference(self, url: str, ref_type: ExternalReferenceType = ExternalReferenceType.BOM, 
							   comment: str | None = None) -> None:
		""" Add an external reference to the main component or service in this XBOM
		
			External references are used to link to other BOMs that contain related components.
			This is useful when each component is in a dedicated BOM and we want to reference it.
		
			:param url: URL or URI of the external reference (can be a bom_ref of another XBOM)
			:param ref_type: Type of external reference (default: BOM)
			:param comment: Optional comment describing the external reference
			:return: None
		"""
		if self.bom is None:
			raise ValueError("Cannot add external reference to an empty BOM")
		
		main_item = self.get_main_item()
		if main_item is None:
			raise ValueError("XBOM must contain exactly one Component or Service to add an external reference")
		
		ext_ref = ExternalReference(
			type=ref_type,  # type: ignore[call-arg]
			url=XsUri(url),  # type: ignore[call-arg]
			comment=comment  # type: ignore[call-arg]
		)
		
		# Add external reference to the component/service
		main = cast(Any, main_item)
		if main.external_references is None:
			main.external_references = []
		main.external_references.add(ext_ref)  # type: ignore[union-attr]

	def add_dependency(self, depends_on_ref: 'str | CyclonedxXbom') -> None:
		""" Add a dependency from the main item in this XBOM to another component/service
		
			This creates a CycloneDX dependency relationship where the main item in this XBOM
			depends on the specified component/service (identified by its bom_ref).
		
			:param depends_on_ref: The bom_ref of the item this XBOM depends on, or an Xbom object
			:return: None
		"""
		if self.bom is None:
			raise ValueError("Cannot add dependency to an empty BOM")
		bom = self._ensure_bom()
		
		main_item = self.get_main_item()
		if main_item is None:
			raise ValueError("XBOM must contain exactly one Component or Service to add a dependency")
		
		main = cast(Any, main_item)
		if main.bom_ref is None:
			raise ValueError("Main item must have a bom_ref to add a dependency")
		
		# Get the dependency ref
		if isinstance(depends_on_ref, CyclonedxXbom):
			dep_ref = depends_on_ref.get_bom_ref()
			if dep_ref is None:
				raise ValueError("The XBOM provided as dependency must have a bom_ref")
		else:
			dep_ref = depends_on_ref

		
		# Create the dependency
		dependency = Dependency(ref=main.bom_ref, dependencies=[Dependency(ref=BomRef(dep_ref))])  # type: ignore[call-arg]
		bom.dependencies.add(dependency)

	def add_dependency_with_external_ref(self, depends_on_xbom: 'Xbom', comment: str | None = None) -> None:
		""" Add both an external reference and a dependency to another XBOM
		
			This is a convenience method that adds the dependency XBOM as an external reference
			and creates a dependency relationship. Use this when each component is in a dedicated 
			BOM and you want to express that this XBOM depends on another XBOM.
			
			A stub component is created in this BOM to represent the external dependency,
			with an external reference using the CycloneDX bom-link format:
			urn:cdx:{serial-number}/{version}#{bom-ref}
			See: https://cyclonedx.org/capabilities/bomlink/
		
			:param depends_on_xbom: The XBOM that this XBOM depends on
			:param comment: Optional comment describing the dependency
			:return: None
		"""
		if not isinstance(depends_on_xbom, CyclonedxXbom):
			raise TypeError(f"Expected CyclonedxXbom, got {type(depends_on_xbom)}")
		
		dep_ref = depends_on_xbom.get_bom_ref()
		if dep_ref is None:
			raise ValueError("The dependency XBOM must have a bom_ref")
		
		# Generate a proper CycloneDX bom-link URL
		bom_link = depends_on_xbom.get_bom_link(dep_ref)
		
		# Get info from the dependency's main item to create a stub
		dep_main_item = depends_on_xbom.get_main_item()
		if dep_main_item is None:
			raise ValueError("The dependency XBOM must have a main component or service")
		
		# Create a stub component or service with an external reference to the dependency BOM
		ext_ref = ExternalReference(
			type=ExternalReferenceType.BOM,  # type: ignore[call-arg]
			url=XsUri(bom_link),  # type: ignore[call-arg]
			comment=comment  # type: ignore[call-arg]
		)
		
		dep_main = cast(Any, dep_main_item)
		if isinstance(dep_main_item, Component):
			stub = Component(
				name=dep_main.name,  # type: ignore[call-arg]
				type=dep_main.type,  # type: ignore[call-arg]
				bom_ref=dep_ref,  # type: ignore[call-arg]
				external_references=[ext_ref]  # type: ignore[call-arg]
			)
			self._ensure_bom().components.add(stub)
		elif isinstance(dep_main_item, Service):
			stub = Service(
				name=dep_main.name,  # type: ignore[call-arg]
				bom_ref=dep_ref,  # type: ignore[call-arg]
				external_references=[ext_ref]  # type: ignore[call-arg]
			)
			self._ensure_bom().services.add(stub)
		
		# Add the dependency relationship
		self.add_dependency(dep_ref)


	def merge(self, other: 'Xbom') -> None:
		""" Merge another XBOM into this one
		
			Handles stub components/services specially to avoid duplicates.
			Stubs are identified by having an external reference of type BOM.
			When merging, stubs with the same bom_ref or same external BOM URL
			are deduplicated.

			:param other: Other XBOM to merge
			:return: None
		"""
		if not isinstance(other, CyclonedxXbom):
			raise TypeError(f"Can only merge CyclonedxXbom instances, got {type(other)}")
		
		if other.bom is None or self.bom is None:
			return
		bom = self._ensure_bom()
		other_bom = other._ensure_bom()

		if self.format != other.format:
			raise ValueError(f"Cannot merge XBOMs with different formats: {self.format} != {other.format}")

		# Local helper functions
		def is_stub(item: Any) -> bool:
			if item.external_references:
				for ref in item.external_references:
					if ref.type == ExternalReferenceType.BOM:
						return True
			return False

		def get_ref_value(item: Any) -> str | None:
			# Handle Dependency objects (use 'ref') and Component/Service (use 'bom_ref')
			for attr in ('ref', 'bom_ref'):
				if hasattr(item, attr) and getattr(item, attr) is not None:
					val = getattr(item, attr)
					return val.value if hasattr(val, 'value') else str(val)
			return None

		def get_bom_urls(item: Any) -> set[str]:
			urls: set[str] = set()
			if item.external_references:
				for ref in item.external_references:
					if ref.type == ExternalReferenceType.BOM:
						urls.add(str(ref.url))
			return urls

		# Build sets of existing bom_refs and external BOM URLs for deduplication
		existing_component_refs: set[str] = set()
		existing_component_bom_urls: set[str] = set()
		for comp in bom.components:
			ref = get_ref_value(comp)
			if ref:
				existing_component_refs.add(ref)
			if is_stub(comp):
				existing_component_bom_urls.update(get_bom_urls(comp))

		existing_service_refs: set[str] = set()
		existing_service_bom_urls: set[str] = set()
		for svc in bom.services:
			ref = get_ref_value(svc)
			if ref:
				existing_service_refs.add(ref)
			if is_stub(svc):
				existing_service_bom_urls.update(get_bom_urls(svc))

		# Merge components, handling stubs specially
		for component in other_bom.components:
			comp_ref = get_ref_value(component)
			
			if is_stub(component):
				# For stubs, check both bom_ref and external BOM URLs
				if comp_ref and comp_ref in existing_component_refs:
					continue  # Skip duplicate stub by bom_ref
				comp_urls = get_bom_urls(component)
				if comp_urls & existing_component_bom_urls:
					continue  # Skip duplicate stub by external URL
				# Add new stub and track it
				if comp_ref:
					existing_component_refs.add(comp_ref)
				existing_component_bom_urls.update(comp_urls)
			else:
				# For non-stubs, just check bom_ref
				if comp_ref and comp_ref in existing_component_refs:
					continue  # Skip duplicate component
				if comp_ref:
					existing_component_refs.add(comp_ref)
			
			bom.components.add(component)

		# Merge services, handling stubs specially
		for service in other_bom.services:
			svc_ref = get_ref_value(service)
			
			if is_stub(service):
				# For stubs, check both bom_ref and external BOM URLs
				if svc_ref and svc_ref in existing_service_refs:
					continue  # Skip duplicate stub by bom_ref
				svc_urls = get_bom_urls(service)
				if svc_urls & existing_service_bom_urls:
					continue  # Skip duplicate stub by external URL
				# Add new stub and track it
				if svc_ref:
					existing_service_refs.add(svc_ref)
				existing_service_bom_urls.update(svc_urls)
			else:
				# For non-stubs, just check bom_ref
				if svc_ref and svc_ref in existing_service_refs:
					continue  # Skip duplicate service
				if svc_ref:
					existing_service_refs.add(svc_ref)
			
			bom.services.add(service)

		# Merge dependencies, deduplicating by ref
		existing_dep_refs: set[str] = set()
		for dep in bom.dependencies:
			ref = get_ref_value(dep)
			if ref:
				existing_dep_refs.add(ref)

		for dependency in other_bom.dependencies:
			dep_ref = get_ref_value(dependency)
			if dep_ref and dep_ref in existing_dep_refs:
				continue  # Skip duplicate dependency
			if dep_ref:
				existing_dep_refs.add(dep_ref)
			bom.dependencies.add(dependency)

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
		bom = self._ensure_bom()

		match self.format:
			case SbomFormat.cyclonedx:
				serializer = JsonV1Dot7(bom)
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
				self.bom = Bom.from_json(json.loads(data))  # type: ignore[attr-defined]
			case _:
				raise NotImplementedError(f"Deserialization for format {self.format} is not implemented.")

	def __repr__(self):
		if self.bom is None:
			return f"CyclonedxXbom(format={self.format}, bom=None)"
		bom = self._ensure_bom()
		return f"CyclonedxXbom(format={self.format}, bom=({len(bom.services)} services, {len(bom.components)} components))"

	def __str__(self):
		if self.bom is None:
			return (f"CyclonedxXbom(format={self.format}, bom=None)")
		bom = self._ensure_bom()

		match self.format:
			case SbomFormat.cyclonedx:
				return (f"CyclonedxXbom("
						f"format={self.format}, "
						f"bom_metadata={bom.metadata}, "
						f"components_count={len(bom.components)}, "
						f"services_count={len(bom.services)})")
			case _:
				return (f"CyclonedxXbom(format={self.format}, bom=Unknown format)")


# Register CyclonedxXbom in the format registry for polymorphic deserialization
_XBOM_FORMAT_REGISTRY[SbomFormat.cyclonedx] = CyclonedxXbom