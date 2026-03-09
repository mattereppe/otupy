from otupy.profiles.ctxd.data.ctxd_object import CTXDObject


class Cloud(CTXDObject):
	"""Cloud
    it is the description of the service - Cloud
	"""
	type: str = None
	""" type of the cloud service"""


	def __init__(self, cloud = None, description = None, id = None, name = None, type = None):
		if isinstance(cloud, Cloud):
			super().__init__(name=cloud.name, description=cloud.description, id=cloud.id)
			self.type = cloud.type
		else:
			super().__init__(name=name, description=description, id=id)
			self.type = type 

	def get_subtype(self):
		""" This function might be replace in the future by
			providing type classes like for other services."""
		return self.type

	def __repr__(self):
		return (f"Cloud(description={self.description}, id={self.id}, "
	             f"name={self.name}, type={self.type})")
	
	def __str__(self):
		return self.__repr__()
