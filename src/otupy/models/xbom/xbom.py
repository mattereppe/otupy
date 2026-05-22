from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from otupy.models.ctxd import Service, Link
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.xbom_encoding import XbomEncoding

# Registry mapping XbomFormat to concrete Xbom subclasses
# This is populated by subclasses when they are imported
_XBOM_FORMAT_REGISTRY: dict[XbomFormat, type['Xbom']] = {}


class Xbom(ABC):
	""" Abstract base class for managing eXtended Bill of Materials (XBOM)
	
	This abstract class defines the minimal interface that all XBOM implementations must follow.
	Actuators work with this interface, allowing different BOM formats to be used
	interchangeably without changes to the actuator code.
	
	Only methods used by actuators are abstracted here. Format-specific methods
	remain in the concrete implementations.
	"""
	
	format: XbomFormat = None  # type: ignore
	""" Format of the XBOM. Subclasses must define this field with a concrete value."""

	def __init__(self):
		self.xbom = None
	
	def __init_subclass__(cls, **kwargs):
		""" Automatic registration of concrete class definitions """
		super().__init_subclass__(**kwargs)

		if cls.format is None:
			raise TypeError(f"{cls.__name__} must define 'format'")

		_XBOM_FORMAT_REGISTRY[cls.format] = cls

	@staticmethod
	def get(format: XbomFormat):
		""" Get the Xbom class

			Returns the class corresponding to the required format.
			:params format: Format of the Xbom required.
			:returns: A class that implements the Xbom format requested.
		"""
		return _XBOM_FORMAT_REGISTRY.get(format, None)

	@abstractmethod
	def create(self, services: list[Service] = [], links: list[Link] = []) -> Any:
		""" Create the Xbom

			Creates a Xbom of the given format from the list of Services and Links of
			the ctxd data model. The Xbom is returned in the required format, and also
			kept internally for following operations. The invocation of this method
			discards a previously created Xbom.

			:param services: A list of otupy ``Service``.
			:param links: A list of otupy ``Link``.
			:return: Return the Xbom created.
		"""
		pass

	def load(self, xbom: Any) -> None:
		""" Load an existing Xbom 

			Loads an existing xbom of the same format as managed by the class.

			:param xbom: The xbom to store internally.
		"""
		self.xbom = xbom


	@abstractmethod
	def serialize(self, encoding: XbomEncoding = None) -> str:
		""" Serialize the Xbom

			Serializes the Xbom in the provided encoding scheme.
			If no Xbom has been previously generated, should return an empty string.

			:param encoding: The serialization scheme to be used. 
			:return: A string containing the encoded Xbom.
		"""
		pass

	@abstractmethod
	def deserialize(self, xbom: str, encoding: XbomEncoding = None) -> Any:
		""" Deserialize a Xbom

			Deserialises a Xbom, stores it internally and returns the Xbom in its
			format, using the class registered in otupy for that format. 
			Any Xbom previously created, loaded, or deserialized is dropped.

			:param xbom: The encoded Xbom.
			:param encoding: The serialization method used to encode the provided Xbom.
			:return: The Xbom in its native format.
		"""
		pass

	@abstractmethod
	def summary(self) -> str:
		""" Get human readable summary of the bom content

			Creates a human-readable summary of the bom. Most of the times, this should
			include the short identifiers for components and dependencies, also including
			the bom that originaged them.

			Implementation are suitable to provide the format they prefer, as well as to
			use parameters to select among different formats.
		"""
		pass
