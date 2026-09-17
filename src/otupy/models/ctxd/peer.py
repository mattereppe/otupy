import otupy.types.base
from otupy.models.ctxd.name import Name
from otupy.models.ctxd.service import SId
from otupy.models.ctxd.consumer import Consumer
from otupy.models.ctxd.peer_role import PeerRole

class Peer(otupy.types.base.Record):
	"""Peer
    Service connected on the other side of the link
	"""
	
	service_name: Name = None
	""" Name of the service """
	sid:SId = None
	""" Id of the service """
	role: PeerRole = None
	""" Role of this Peer in the link """
	consumer: Consumer = None
	""" Consumer connected on the other side of the link """


	def __init__(self, peer:object = None, service_name:Name = None, sid:SId = None, role:PeerRole = None, consumer:Consumer = None):
		if peer is not None:
			self.service_name = peer.service_name 
			self.sid = peer.sid
			self.role = peer.role 
			self.consumer = peer.consumer 
		else:
			self.service_name = Name(service_name) if service_name is not None else None
			self.sid = sid
			try:
				self.role = PeerRole[role] if role is not None else None
			except:
				self.role = PeerRole(role) if role is not None else None
			if isinstance(consumer, dict):
				self.consumer = Consumer(**consumer) if consumer is not None else None
			else:
				self.consumer = Consumer(consumer) if consumer is not None else None

	def __repr__(self):
		return (f"Peer(service_name={self.service_name}, sid={self.sid}, role={self.role},"
	             f"consumer={self.consumer})")
	
	def __str__(self):
		return self.__repr__()

