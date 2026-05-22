from otupy.models.ctxd.network_function import NetworkFunction

from otupy.profiles.xbom.data.network_function_type import NetworkFunctionType
from cyclonedx.model import Property
from cyclonedx.model.service import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> any: # type: ignore
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
		cdx_service = wrapped_function.to_cyclonedx() if hasattr(wrapped_function, 'to_cyclonedx') else None
		
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

NetworkFunction.to_cyclonedx = to_cyclonedx
