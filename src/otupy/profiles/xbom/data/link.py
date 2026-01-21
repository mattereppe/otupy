from typing import List
import uuid

import otupy.types.base
from otupy.profiles.xbom.data.peer import Peer
from otupy.profiles.xbom.data.link_type import LinkType
from otupy.profiles.xbom.data.name import Name
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf
from otupy.core.version import Version
from cyclonedx.model import Property


class Link(otupy.types.base.Record):
	"""Link

		A Link is a relationship between Services. The Link class contains all Peers of a given LinkType for the given service Name.
		Implementations might instantiate multiple Links for different Peers of the same LinkType or provide all Peers in the same instance.
	"""

	name: Name = None
	""" Id of the link """
	description: str = None
	""" Generic description of the relationship"""
	versions: ArrayOf(Version) = None # type: ignore
	""" Subset of service features used in this relationship (where applicable). E.g.: the version of an API, or of a Network protocol."""
	link_type: LinkType = None
	""" Type of the link"""
	peers: ArrayOf(Peer) = None # type: ignore
	""" Services connected on the link """

	def __init__(self, name:Name = None, description:str = None, versions:ArrayOf(Version) = None, link_type:LinkType = None, # type: ignore
			   peers:ArrayOf(Peer) = None): # type: ignore
		if isinstance(name, Link):
			self._init_from_link(name)
		else:
			self._init_from_params(name, description, versions, link_type, peers) 
		self.validate_fields()

	def _init_from_link(self, link):
		self.name = link.name if link.name is not None else None
		self.description = link.description if link.description is not None else None
		self.versions = link.versions if link.versions is not None else None
		self.link_type = link.link_type if link.link_type is not None else None
		self.peers = link.peers if link.peers is not None else None

	def _init_from_params(self, name = None, description = None, versions = None, link_type = None, peers = None):
		self.name = name if name is not None else None
		self.description = description if description is not None else None
		self.versions = versions if versions is not None else None
		self.link_type = link_type if link_type is not None else None
		self.peers = peers if peers is not None else None

	def __repr__(self):
		return (f"Link(name={self.name}, "
                 f"description={self.description}, versions={self.versions}, link_type={self.link_type}, peers={self.peers}")
	
	def __str__(self):
		return f"Link(" \
	            f"name={self.name}, " \
	            f"description={self.description}, " \
				f"versions={self.versions}, " \
				f"link_type={self.link_type}, " \
				f"peers={self.peers}" 

	def validate_fields(self):
		if self.name is not None and not isinstance(self.name, Name):
			raise TypeError(f"Expected 'name' to be of type {Name}, but got {type(self.name)}")
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.versions is not None and not isinstance(self.versions, Array):
			raise TypeError(f"Expected 'versions' to be of type {Array}, but got {type(self.versions)}")
		if self.link_type is not None and not isinstance(self.link_type, LinkType):
			raise TypeError(f"Expected 'link_type' to be of type {LinkType}, but got {type(self.link_type)}")
		if self.peers is not None and not isinstance(self.peers, Array):
			raise TypeError(f"Expected 'peers' to be of type {Array}, but got {type(self.peers)}")

	def as_cyclonedx(self, link_id: str = str(uuid.uuid4())) -> List[Property]:
		"""Convert Link to CycloneDX properties format.
		
		Args:
			link_id: The unique identifier for this link.
		
		Returns:
			List[Property]: List of CycloneDX Property objects.
		"""
		properties = [
			Property(name="otupy:link:id", value=link_id)
		]
		
		if self.description is not None:
			properties.append(Property(name=f"otupy:link:{link_id}:desc", value=self.description))
		if self.versions is not None and len(self.versions) > 0:
			properties.append(Property(name=f"otupy:link:{link_id}:version", value=str(self.versions[0])))
		if self.link_type is not None:
			properties.append(Property(name=f"otupy:link:{link_id}:type", value=self.link_type.name.lower()))
		
		# Add peer properties
		if self.peers is not None:
			for peer in self.peers:
				peer_props = peer.as_cyclonedx(prefix=f"otupy:link:{link_id}:peer")
				properties.extend(peer_props)
		
		return properties
