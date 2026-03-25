from otupy import Record
from otupy.profiles.xbom.data.network_function_type import NetworkFunctionType
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.profiles.xbom.data.xbom_object import XBOMObject


class NetworkFunction(XBOMObject):
	"""Network Function

		A network function process network packets for both forwarding and security purposes.
		It can be hosted on baremetal devices, general purpose computers, containers, and other
		virtualization mechanisms (e.g., Linux namespaces). In these terms, the same model applies
		for both legacy network devices and Network Virtual Functions.
	"""
	type: NetworkFunctionType = None
	""" Type of the network function, including more complex data objects. """
	version: str = None
	""" Version/release of this function """


	def __init__(self, 
			name:str = None, 
			id:str = None, 
			description:str = None, 
			version:str = None, 
			type:NetworkFunctionType = None):
		if isinstance(name, NetworkFunction):
			self.name = name.name
			self.id = name.id
			self.description = name.description
			self.version = name.version
			self.type = name.type
		else:
			self.name = str(name) if name is not None else None
			self.id = str(id) if id is not None else None
			self.description = str(description) if description is not None else None
			self.version = str(version) if version is not None else None
			self.type = type if type is not None else None

	def __repr__(self):
		return (f"NetworkFunction( {super().__repr__()}, \
					version={self.version}, \
					type={self.type.getObj() if self.type else None})")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> any: # type: ignore
		"""Convert NetworkFunction to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		if self.type is None:
			cdx_service = Service(
				name=self.name or "unknown",
				bom_ref=generate_bom_ref("network_function"),
				description=self.description
			)
		else:
			wrapped_function = self.type.getObj()
			cdx_service = wrapped_function.as_cyclonedx() if hasattr(wrapped_function, 'as_cyclonedx') else None
			
			if cdx_service is None:
				cdx_service = Service(
					name=self.name or "unknown",
					bom_ref=generate_bom_ref("network_function"),
					description=self.description
				)
			else:
				if self.name is not None:
					cdx_service.name = str(self.name)
				if getattr(self, "description", None) is not None:
					cdx_service.description = str(self.description)

		properties = [
			Property(name="otupy:type", value="network_function")
		]
		if self.version is not None:
			properties.append(Property(name="otupy:network_function:version", value=self.version))
		if self.id is not None:
			properties.append(Property(name="otupy:netfunc:id", value=self.id))
		if self.type is not None:
			type_name = self.type.getName() if hasattr(self.type, 'getName') else str(self.type)
			properties.append(Property(name="otupy:netfunc:type", value=type_name))
		
		if hasattr(cdx_service, 'properties') and cdx_service.properties is not None:
			cdx_service.properties.update(properties)
		else:
			cdx_service.properties = properties
		
		return cdx_service
