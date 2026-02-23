from typing import List

import otupy.types.base
from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.consumer import Consumer
from otupy.profiles.xbom.data.peer_role import PeerRole
from cyclonedx.model import Property

class Peer(otupy.types.base.Record):
	"""Peer
    Service connected on the other side of the link
	"""
	
	service_name: Name = None
	""" Id of the service """
	role: PeerRole = None
	""" Role of this Peer in the link """
	consumer: Consumer = None
	""" Consumer connected on the other side of the link """


	def __init__(self, service_name:Name = None, role:PeerRole = None, consumer:Consumer = None):
		if(isinstance(service_name, Peer)):
			self.service_name = service_name.service_name if service_name.service_name is not None else None
			self.role = service_name.role if service_name.role is not None else None
			self.consumer = service_name.consumer if service_name.consumer is not None else None	
		else:
			self.service_name = Name(service_name) if service_name is not None else None
			try:
				self.role = PeerRole[role] if role is not None else None
			except:
				self.role = PeerRole(role) if role is not None else None
			if isinstance(consumer, dict):
				self.consumer = Consumer(**consumer) if consumer is not None else None
			else:
				self.consumer = Consumer(consumer) if consumer is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Peer(service_name={self.service_name}, role={self.role},"
	             f"consumer={self.consumer}")
	
	def __str__(self):
		return f"Peer(" \
	            f"service_name={self.service_name.getObj()}, " \
					f"role={self.role}, " \
	            f"consumer={self.consumer}" 

	def validate_fields(self):
		if self.service_name is not None and not isinstance(self.service_name, Name):
			raise TypeError(f"Expected 'service_name' to be of type {Name}, but got {type(self.service_name)}")
		if self.role is not None and not isinstance(self.role, PeerRole):
			raise TypeError(f"Expected 'role' to be of type {PeerRole}, but got {type(self.role)}")		
		if self.consumer is not None and not isinstance(self.consumer, Consumer):
			raise TypeError(f"Expected 'consumer' to be of type {Consumer}, but got {type(self.consumer)}")

	def as_cyclonedx(self, prefix: str = "otupy:peer") -> List[Property]:
		"""Convert Peer to CycloneDX properties format.
		
		Args:
			prefix: The prefix to use for property names.
		
		Returns:
			List[Property]: List of CycloneDX Property objects.
		"""
		properties = []
		
		service_name_str = str(self.service_name.getObj()) if self.service_name is not None else "unknown"
		
		properties.append(Property(name=f"{prefix}:service-name", value=service_name_str))
		
		if self.role is not None:
			properties.append(Property(name=f"{prefix}:{service_name_str}:role", value=self.role.name.lower()))
		
		# Add consumer properties
		if self.consumer is not None:
			consumer_props = self.consumer.as_cyclonedx(prefix=f"{prefix}:{service_name_str}:consumer")
			properties.extend(consumer_props)
		
		return properties
