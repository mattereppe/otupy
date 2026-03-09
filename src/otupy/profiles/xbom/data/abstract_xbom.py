from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from otupy.types.base import Record
from otupy.profiles.xbom.data.xbom_format import XbomFormat

if TYPE_CHECKING:
	from cyclonedx.model.component import Component
	from cyclonedx.model.service import Service

# Registry mapping XbomFormat to concrete Xbom subclasses
# This is populated by subclasses when they are imported
_XBOM_FORMAT_REGISTRY: dict[XbomFormat, type['Xbom']] = {}


class Xbom(Record, ABC):
	"""Abstract base class for eXtended Bill of Materials (XBOM)
	
	This abstract class defines the minimal interface that all XBOM implementations must follow.
	Actuators work with this interface, allowing different BOM formats to be used
	interchangeably without changes to the actuator code.
	
	Only methods used by actuators are abstracted here. Format-specific methods
	remain in the concrete implementations.
	"""
	
	format: XbomFormat = None  # type: ignore
	""" Format of the XBOM """
	
	bom: Any = None
	""" Bill of Materials object (format-specific) """

	@classmethod
	def fromdict(clstype, dic, e):
		"""Polymorphic deserialization for Xbom subclasses
		
		When deserializing to the abstract Xbom type, this method inspects the 'format'
		field to determine the correct concrete subclass to use.
		
		:param dic: The dictionary representation
		:param e: The encoder being used
		:return: An instance of the appropriate concrete Xbom subclass
		"""
		# If we're deserializing directly to Xbom (not a subclass), 
		# we need to determine the concrete type from the format field
		if clstype is Xbom:
			if isinstance(dic, dict) and 'format' in dic:
				format_value = dic.get('format')
				# Convert format value to XbomFormat enum if it's a string or int
				if isinstance(format_value, str):
					format_enum = XbomFormat[format_value]
				elif isinstance(format_value, int):
					format_enum = XbomFormat(format_value)
				elif isinstance(format_value, XbomFormat):
					format_enum = format_value
				else:
					format_enum = XbomFormat.cyclonedx  # Default
				
				# Look up the concrete class for this format
				concrete_class = _XBOM_FORMAT_REGISTRY.get(format_enum)
				if concrete_class is not None:
					return concrete_class.fromdict(dic, e)
			
			# Default to CyclonedxXbom if format not specified or not found
			from otupy.profiles.xbom.data.xbom import CyclonedxXbom
			return CyclonedxXbom.fromdict(dic, e)
		
		# For concrete subclasses, use the normal Record.fromdict
		return Record.fromdict(dic, e)

	@abstractmethod
	def add(self, item: Any) -> None:
		"""
        Adds an item to the XBOM.
        This method must implement the logic to handle the different types of items 
        that can be added to the XBOM. It should integrate other classes defined 
        within this folder by invoking their respective `as_*` methods to ensure 
        the item is correctly processed before addition.
        :param item: The item to be added.
		:return: None
		"""
		pass

	@abstractmethod
	def find_ref_by_name(self, name: str) -> str | None:
		"""Find the bom_ref of a component or service by name

		:param name: The name of the component or service to find
		:return: The bom_ref string if found, None otherwise
		"""
		pass

	@abstractmethod
	def add_dependency(self, parent_ref: str, child_ref: str) -> None:
		"""Add a dependency relationship

		Creates a dependency where child_ref depends on parent_ref.

		:param parent_ref: The bom_ref of the item that is depended upon
		:param child_ref: The bom_ref of the dependent item
		:return: None
		"""
		pass

	@abstractmethod
	def add_dependency_with_external_ref(self, depends_on_xbom: 'Xbom', from_ref: str, comment: str | None = None) -> None:
		"""Add both an external reference and a dependency to another XBOM
		
		:param depends_on_xbom: The XBOM that this XBOM depends on
		:param from_ref: The bom_ref of the item in this BOM that depends on the other
		:param comment: Optional comment describing the dependency
		:return: None
		"""
		pass

