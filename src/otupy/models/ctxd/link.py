import otupy.types.base
from otupy.models.ctxd.service import SId
from otupy.models.ctxd.peer import Peer
from otupy.models.ctxd.peer_role import PeerRole
from otupy.models.ctxd.link_type import LinkType
from otupy.models.ctxd.name import Name
from otupy.types.base.array import Array
from otupy.types.base.array_of import ArrayOf
from otupy.core.version import Version


class Link(otupy.types.base.Record):
	"""Link

		A Link is a relationship between Services. A relationship is made between a subject (the ``name``) and one
		or more objects (the ``peers``). 

		The Link class contains all Peers of a given LinkType for the given service Name.
		Implementations might instantiate multiple Links for different Peers of the same LinkType or provide all Peers in the same instance.


	"""

	name: Name = None
	""" Id of the link """
	sid: SId = None
	""" Service ID of the owner of this link """
	description: str = None
	""" Generic description of the relationship"""
	link_type: LinkType = None
	""" Type of the link"""
	role: PeerRole = None
	""" Role of service  in the link relationship """
	peers: ArrayOf(Peer) = None # type: ignore
	""" Services connected on the link """

	def __init__(self, link:object = None, name:Name = None, sid:SId = None, description:str = None, link_type:LinkType = None, 
			   role:PeerRole = None, peers:ArrayOf(Peer) = None): # type: ignore
		if link is not None:
			self._init_from_link(link)
		else:
			self._init_from_params(name, sid, description, link_type, role, peers) 
		self.validate_fields()

	def _init_from_link(self, link):
		self.name = link.name 
		self.sid  = link.sid
		self.description = link.description 
		self.role = link.role 
		self.link_type = link.link_type 
		self.peers = link.peers 

	def _init_from_params(self, name = None, sid = None, description = None, link_type = None, role = None, peers = None):
		self.name = Name(name) if name is not None else None
		self.sid = sid
		self.description = description 
		self.role = role 
		self.link_type = link_type 
		if peers is not None: 
			self.peers = ArrayOf(Peer)() 
			for p in peers:
				if isinstance(p, dict):
					self.peers.append(Peer(**p))
				else:
					self.peers.append(Peer(p))
		else: 
			self.peers = None

	def __repr__(self):
		return (f"Link(name={self.name.getObj()}, sid={self.sid}, "
                 f"description={self.description}, role={self.role}, link_type={self.link_type}, peers={self.peers}")
	
	def __str__(self):
		return f"Link(" \
	            f"name={self.name.getObj()}, " \
	            f"description={self.description}, " \
					f"role={self.role}, " \
					f"link_type={self.link_type}, " \
					f"peers={self.peers}" 

	def validate_fields(self):
		if self.name is not None and not isinstance(self.name, Name):
			raise TypeError(f"Expected 'name' to be of type {Name}, but got {type(self.name)}")
		if self.description is not None and not isinstance(self.description, str):
			raise TypeError(f"Expected 'description' to be of type {str}, but got {type(self.description)}")
		if self.role is not None and not isinstance(self.role, PeerRole):
			raise TypeError(f"Expected 'role' to be of type {PeerRole}, but got {type(self.role)}")
		if self.link_type is not None and not isinstance(self.link_type, LinkType):
			raise TypeError(f"Expected 'link_type' to be of type {LinkType}, but got {type(self.link_type)}")
		if self.peers is not None and not isinstance(self.peers, Array):
			raise TypeError(f"Expected 'peers' to be of type {Array}, but got {type(self.peers)}")
