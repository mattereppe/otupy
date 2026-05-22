from typing import List
from otupy.models.ctxd.peer import Peer

from cyclonedx.model import Property
from otupy.profiles.xbom.data.service import SId
from otupy.types.base.record import Record

def to_cyclonedx(self, prefix: str = "otupy:peer") -> List[Property]:
	"""Convert Peer to CycloneDX properties format.
	
	Args:
		prefix: The prefix to use for property names.
	
	Returns:
		List[Property]: List of CycloneDX Property objects.
	"""
	properties = []
	
	sid = str(self.sid) if self.sid is not None else self.service_name.getObj() if self.service_name is not None else "unknown"
	properties.append(Property(name=f"{prefix}:sid", value=sid))
	
	if self.role is not None:
		properties.append(Property(name=f"{prefix}::{sid}::role", value=self.role.name.lower()))
	
	# Add consumer properties
	if self.consumer is not None:
		consumer_props = self.consumer.to_cyclonedx(prefix=f"{prefix}:{sid}:consumer")
		properties.extend(consumer_props)
	
	return properties

Peer.to_cyclonedx = to_cyclonedx
