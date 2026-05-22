from typing import List
from otupy.models.ctxd.link import Link
from otupy.models.xbom.cyclonedx.bom_ref import generate_uuid

from cyclonedx.model import Property

def to_cyclonedx(self, link_id: str|None = None) -> List[Property]:
	"""Convert Link to CycloneDX properties format.
	
	Args:
		link_id: The unique identifier for this link. If None, a UUID will be generated.
	
	Returns:
		List[Property]: List of CycloneDX Property objects.
	"""
	if link_id is None:
		link_id = generate_uuid()
	
	properties = [
		Property(name="otupy:link:id", value=link_id)
	]
	
	if self.description is not None:
		properties.append(Property(name=f"otupy:link::{link_id}::desc", value=self.description))
	if self.role is not None:
		properties.append(Property(name=f"otupy:link::{link_id}::role", value=self.role.name.lower()))
	if self.link_type is not None:
		properties.append(Property(name=f"otupy:link::{link_id}::type", value=self.link_type.name.lower()))
	
	# Add peer properties
	if self.peers is not None:
		for peer in self.peers:
			peer_props = peer.to_cyclonedx(prefix=f"otupy:link::{link_id}::peer")
			properties.extend(peer_props)
	
	return properties

Link.to_cyclonedx = to_cyclonedx
