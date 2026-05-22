from otupy.models.ctxd import Service
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

from cyclonedx.model import Property
from cyclonedx.model.service import Service as CycloneDXService

def to_cyclonedx(self) -> any: # type: ignore
	"""Convert Service to CycloneDX service format.
	
	Returns:
		Service: CycloneDX Service, component or anything 
	"""
	if self.type is None:
		raise ValueError(f"Service {self.name.getObj() if self.name else None} has no type, cannot convert to CycloneDX format.")
	wrapped_service = self.type.getObj() if self.type is not None else "unknown"
	cdx_service = wrapped_service.to_cyclonedx() if hasattr(wrapped_service, 'to_cyclonedx') else None
	if cdx_service is None:
		raise ValueError(f"Cannot convert service of type {self.type} to CycloneDX format. Missing 'to_cyclonedx' method.")
	if self.name is not None:
		cdx_service.name = str(self.name.getObj())
	
	properties = list()
	# if self.sid is not None:
	# 	properties.append(Property(name="otupy:service:sid", value=str(self.sid)))
	if self.domain is not None:
		properties.append(Property(name="otupy:service:domain", value=self.domain))
	if self.namespace is not None:
		properties.append(Property(name="otupy:service:namespace", value=self.namespace))
	if self.owner is not None:
		properties.append(Property(name="otupy:service:owner", value=self.owner))
	if self.release is not None:
		properties.append(Property(name="otupy:service:release", value=self.release))
	
	if hasattr(cdx_service, 'properties') and cdx_service.properties is not None:
		cdx_service.properties.update(properties)
	else:
		cdx_service.properties = properties

	# Overwrite bom_ref with SId if available
	if self.sid is not None:
		cdx_service.bom_ref.value = str(self.sid)
	
	return cdx_service
	
Service.to_cyclonedx = to_cyclonedx
