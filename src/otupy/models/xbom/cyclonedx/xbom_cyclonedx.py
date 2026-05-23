import copy
import logging
import json
import uuid

import otupy 
import otupy.models.ctxd as ctxd

from otupy.models.xbom.xbom import Xbom
from otupy.profiles.xbom import XbomFormat, XbomEncoding

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

from typing import Any, List

logger = logging.getLogger(__name__)

_cyclonedx_schema_version = SchemaVersion.V1_7

class CyclonedxXbom(Xbom):
	""" Cyclonedx Xbom format

		This class maps the Xbom interface to Cyclone DX operations.	
	"""

	format = XbomFormat.cyclonedx

	def create(self, services: otupy.ArrayOf(ctxd.Service) = [], links: otupy.ArrayOf(ctxd.Link) = [], consumer: ctxd.Consumer=None) -> any:
		""" Create the Xbom

			Creates a Cyclone DX Xbom from the list of Services and Links.

			:param services: A list of otupy ``Service``.
			:param links: A list of otupy ``Link``.
			:param consumer: The actuator that is generating this Xbom.
			:return: Return the Xbom created.
		"""
		self.xbom = Bom()
	
		# Add all services to the single BOM
		for service in services:
			logger.debug("Adding %s services to the BOM", len(services))
			if service.type is None:
				logger.warning("Service %s has no type, skipping", service.name)
				continue
			try:
				self._add_service_to_bom(service)
			except Exception as e:
				logger.error("Faulty service infos: %s", service)
				logger.error("Error adding service %s to BOM: %s", service.name, e)

		# TODO: Can be inserted in the previous loop?
		for service in services:
			if service.subservices is not None and len(service.subservices) > 0:
				for subservice in service.subservices:
					if subservice is not None:
						logger.debug("Adding dependency from %s to subservice %s", service.name, subservice)
						try:
							self._add_dependency(parent_ref=str(service.sid), child_ref=str(subservice))
						except ValueError as e:
							logger.warning("Skipping dependency: %s", e)

		# # Add links as properties to the matching services/components
		logger.debug("Adding %d links to the BOM", len(links))
		for link in links:
			self._add_link_to_bom(link, services)

		return self.xbom


	def serialize(self, encoding: XbomEncoding) -> str:
		""" Serialize the Xbom

			Serializes the Xbom in the provided encoding scheme.
			If no Xbom has been previously generated, should return an empty string.

			:param encoding: The serialization scheme to be used. 
			:return: A string containing the encoded Xbom.
		"""
		if self.xbom is None:
			return ""

		match encoding:
			case XbomEncoding.json:
				serializer = JsonV1Dot7(self.xbom)
				return serializer.output_as_string()
			case _:
				raise NotImplementedError(f"Serialization for format {encoding} is not implemented.")


	def deserialize(self, xbom: str, encoding: XbomEncoding) -> any:
		""" Deserialize a Xbom

			Deserialises a Xbom, stores it internally and returns the Xbom in its
			format, using the class registered in otupy for that format. 
			Any Xbom previously created, loaded, or deserialized is dropped.

			:param xbom: The encoded Xbom.
			:param encoding: The serialization method used to encode the provided Xbom.
			:return: The Xbom in its native format.
		"""
		match encoding:
			case XbomEncoding.json:
				validator = JsonStrictValidator(schema_version=_cyclonedx_schema_version)
				err = validator.validate_str(xbom)
				if err:
					raise ValueError("Invalid CycloneDX JSON data: " + str(err))
				self.xbom = Bom.from_json(json.loads(xbom))
			case _:
				raise NotImplementedError(f"Deserialization for format {self.format} is not implemented.")

		return self.xbom

	def summary(self) -> str:
		return self.__str__()


	def _add_service_to_bom(self, item: Component | Service | Dependency | Any ) -> None:
		""" Add item to the BOM

			:param item: Item to add (Component, Service, or object with to_cyclonedx() method)
			:return: None
		"""
		if isinstance(item, Component):
			self.xbom.components.add(item)
			return
		
		if isinstance(item, Service):
			self.xbom.services.add(item)
			return

		if isinstance(item, list):
			for p in item:
				if isinstance(p, Property):
					self._add_service_to_bom(p)
			return

		if hasattr(item, "to_cyclonedx"):
			converted_item = item.to_cyclonedx()
			self._add_service_to_bom(converted_item) # Ricorsione per aggiungerlo come Component o Service
			return
		else:
			raise TypeError(f"Cannot add item of type {type(item)} to XBOM. Expected Component, Service, or object with to_cyclonedx() method.")

	def _add_dependency(self, parent_ref: str, child_ref: str) -> None:
		""" Add a dependency relationship

			Creates a dependency where child_ref depends on parent_ref.

			:param parent_ref: The bom_ref of the item that is depended upon
			:param child_ref: The bom_ref of the dependent item
			:return: None
		"""
		if not parent_ref or not child_ref:
			raise ValueError("Both parent_ref and child_ref must be provided")
		# check that both refs exist in the BOM
		parent_exists = any((comp.bom_ref and comp.bom_ref.value == parent_ref) for comp in self.xbom.components) or \
						any((svc.bom_ref and svc.bom_ref.value == parent_ref) for svc in self.xbom.services)
		child_exists = any((comp.bom_ref and comp.bom_ref.value == child_ref) for comp in self.xbom.components) or \
					   any((svc.bom_ref and svc.bom_ref.value == child_ref) for svc in self.xbom.services)
		if not parent_exists:
			raise ValueError(f"parent_ref '{parent_ref}' does not exist in the BOM")
		if not child_exists:
			raise ValueError(f"child_ref '{child_ref}' does not exist in the BOM")

		dependency = Dependency(ref=BomRef(child_ref), dependencies=[Dependency(ref=BomRef(parent_ref))])
		self.xbom.dependencies.add(dependency)

	def _add_link_to_bom(self, link: ctxd.Link, services: otupy.ArrayOf(ctxd.Service) ) -> None:
		""" Add a link as properties to the matching service/component in the BOM

			:param link: The Link object to add.
		"""
		# Try matching by name first, then fall back to sid
		for service in services:
			if service.sid == link.sid:
				try:
					self._add_link(item_ref=str(service.sid), link=link)
				except Exception as e:
					logger.error("Error adding link %s to service %s: %s", link.name, service.name, e)
				return
		# Fallback: match by sid (name may differ, e.g. short name vs full DNS hostname)
		if link.sid is not None:
			for service in services:
				if service.sid is not None and str(service.sid) == str(link.sid):
					try:
						self._add_link(item_ref=str(service.sid), link=link)
					except Exception as e:
						logger.error("Error adding link %s to service %s: %s", link.sid, service.sid, e)
					return
		logger.warning("Could not find service/component '%s' to add link", link.sid)

	def _add_link(self, item_ref: str, link: any) -> None:
		""" Add a link to an item in the BOM by bom_ref
		
			This is a convenience method that finds the bom_ref of the item by name and adds it as a property.
		
			:param item_name: The name of the item to link to
			:return: None
		"""
		link = link.to_cyclonedx() if hasattr(link, 'to_cyclonedx') else link

		# Look up for the right item to add the link to
		for service in self.xbom.services:
			if service.bom_ref and service.bom_ref.value == item_ref:
				if isinstance(link, list):
					for prop in link:
						service.properties.add(prop)
				else:
					service.properties.add(link)
				return
		for component in self.xbom.components:
			if component.bom_ref and component.bom_ref.value == item_ref:
				if isinstance(link, list):
					for prop in link:
						component.properties.add(prop)
				else:
					component.properties.add(link)
				return

		raise ValueError(f"No component or service with bom_ref '{item_ref}' found in the BOM")

	def _add_dependency_with_external_ref(self, depends_on_xbom: 'Xbom', from_ref: str, comment: str | None = None) -> None:
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
		dep_ref = depends_on_xbom._find_ref_by_name  # we need to get a ref from the other bom
		# Get the first ref from the other BOM's components or services
		dep_bom_ref = None
		if depends_on_xbom.xbom is not None:
			for comp in depends_on_xbom.xbom.components:
				if comp.bom_ref:
					dep_bom_ref = comp.bom_ref.value
					break
			if dep_bom_ref is None:
				for svc in depends_on_xbom.xbom.services:
					if svc.bom_ref:
						dep_bom_ref = svc.bom_ref.value
						break
		if dep_bom_ref is None:
			raise ValueError("The dependency XBOM must have at least one item with a bom_ref")
		
		# Generate a proper CycloneDX bom-link URL
		bom_link = depends_on_xbom._get_bom_link(dep_bom_ref)
		
		# Add external reference pointing to the dependency BOM using bom-link format
		self._add_external_reference(
			target_ref=from_ref,
			url=bom_link,
			ref_type=ExternalReferenceType.BOM,
			comment=comment
		)
		
		# Add the dependency relationship
		self._add_dependency(dep_bom_ref, from_ref)

	def _add_external_reference(self, target_ref: str, url: str, ref_type: ExternalReferenceType = ExternalReferenceType.BOM, 
							   comment: str | None = None) -> None:
		""" Add an external reference to a specific component or service in this XBOM
		
			External references are used to link to other BOMs that contain related components.
		
			:param target_ref: The bom_ref of the component/service to add the reference to
			:param url: URL or URI of the external reference
			:param ref_type: Type of external reference (default: BOM)
			:param comment: Optional comment describing the external reference
			:return: None
		"""
		# Find the item by bom_ref
		target_item = None
		for comp in self.xbom.components:
			if comp.bom_ref and comp.bom_ref.value == target_ref:
				target_item = comp
				break
		if target_item is None:
			for svc in self.xbom.services:
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

	def _get_bom_serial_number(self) -> str:
		""" Get or create the BOM's serial number (UUID)
		
			CycloneDX BOMs have a serial number that uniquely identifies the BOM.
			If not set, a new UUID will be generated and assigned.
		
			:return: The serial number as a UUID string (without 'urn:uuid:' prefix)
		"""
		if self.xbom.serial_number is None:
			# serialize it to force UUID generation
			self.serialize()
			if self.xbom.serial_number is None: # just in case
				self.xbom.serial_number = f"urn:uuid:{uuid.uuid4()}"
		
		# Return just the UUID part (serial_number is already a UUID object)
		return str(self.xbom.serial_number)

	def _get_bom_version(self) -> int:
		""" Get the BOM's version number
		
			:return: The version number (defaults to 1 if not set)
		"""
		if self.xbom is None:
			return 0
		return self.xbom.version if self.xbom.version else 1

	def _get_bom_link(self, element_bom_ref: str) -> str:
		""" Generate a CycloneDX bom-link URI for an element in this BOM
		
			Bom-link format: urn:cdx:{serial-number}/{version}#{bom-ref}
			See: https://cyclonedx.org/capabilities/bomlink/
		
			:param element_bom_ref: The bom-ref of the element.
			:return: A properly formatted bom-link URI
		"""
		serial_number = self._get_bom_serial_number()
		version = self._get_bom_version()
		
		if element_bom_ref is None:
			raise ValueError("Cannot create bom-link without a bom_ref")
		
		return f"urn:cdx:{serial_number}/{version}#{element_bom_ref}"

	def _find_ref_by_name(self, name: str) -> str | None:
		""" Find the bom_ref of a component or service by name

			:param name: The name to search for
			:return: The bom_ref string if found, None otherwise
		"""
		if self.xbom is None:
			return None
		for service in self.xbom.services:
			if service.name == name:
				return service.bom_ref.value if service.bom_ref else None
		for component in self.xbom.components:
			if component.name == name:
				return component.bom_ref.value if component.bom_ref else None
		return None


	def _merge(self, other: 'Xbom') -> None:
		""" Merge another XBOM into this one

			:param other: Other XBOM to merge
			:return: None
		"""
		if other.xbom is None or self.xbom is None:
			return

		if format != other.format:
			raise ValueError(f"Cannot merge XBOMs with different formats: {format} != {other.format}")

		# Merge components
		if other.xbom:
			for component in other.xbom.components:
				self.xbom.components.add(component)

			# Merge services
			for service in other.xbom.services:
				self.xbom.services.add(service)

			# Merge dependencies
			for dependency in other.xbom.dependencies:
				self.xbom.dependencies.add(dependency)

	def __repr__(self):
		return f"Xbom(format={format}, bom=({len(self.xbom.services)} services, {len(self.xbom.components)} components))"


	def __str__(self):
		if self.xbom is None:
			return (f"XBOM(format={format}, bom=None)")

		return (f"XBOM("
					f"format={format}, "
					f"bom_metadata={self.xbom.metadata}, "
					f"components_count={len(self.xbom.components)}, "
					f"services_count={len(self.xbom.services)})")
