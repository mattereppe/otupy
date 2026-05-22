from typing import List

from otupy.models.ctxd.consumer import Consumer

from cyclonedx.model import Property


def to_cyclonedx(self, prefix: str = "otupy:consumer") -> List[Property]:
	"""Convert Consumer to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		List[Property]: List of CycloneDX Property objects.
	"""
	properties = []
	
	if self.host is not None:
		properties.append(Property(name=f"{prefix}:host", value=str(self.host)))
	if self.port is not None:
		properties.append(Property(name=f"{prefix}:port", value=str(self.port)))
	if self.protocol is not None:
		properties.append(Property(name=f"{prefix}:protocol", value=self.protocol.name))
	if self.endpoint is not None:
		properties.append(Property(name=f"{prefix}:endpoint", value=self.endpoint))
	if self.transfer is not None:
		properties.append(Property(name=f"{prefix}:transfer", value=self.transfer.__name__ if hasattr(self.transfer, '__name__') else str(self.transfer)))
	if self.encoding is not None:
		properties.append(Property(name=f"{prefix}:encoding", value=self.encoding.__name__ if hasattr(self.encoding, '__name__') else str(self.encoding)))
	if self.profile is not None:
		properties.append(Property(name=f"{prefix}:profile", value=self.profile))
	if self.actuator is not None:
		for key, value in self.actuator.items():
			properties.append(Property(name=f"{prefix}:actuator:{key}", value=str(value)))
	
	return properties

Consumer.to_cyclonedx = to_cyclonedx
