import otupy.types.base
#from otupy.profiles.ctxd.data.os import OS
#from otupy.types.data.hostname import Hostname

class VM(otupy.types.base.Record):
	"""VM
    it is the description of the service - Virtual Machine
	"""
	description: str = None
	""" Generic description of the VM """
	id: str = None
	""" ID of the VM """
	name: str = None
	""" Name of the VM"""
	image: str = None
	""" Software image loaded in the VM """

	def __init__(self, description:str = None, id:str = None, name:str = None, image:str = None):
		if(isinstance(description, VM)):
			self.description = description.description
			self.id = description.id
			self.name = description.name
			self.image = description.image
		else:
			self.description = description if description is not None else None
			self.id = id if id is not None else None
			self.name = name if name is not None else None
			self.image = image if image is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"VM(description='{self.description}', id={self.id}, "
	             f"name='{self.name}', image={self.image})")
	
	def __str__(self):
		return f"VM(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"image={self.image})"

	def validate_fields(self):
		if self.description is not None and not (isinstance(self.description, str) or isinstance(self.description, VM)):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type str, but got {type(self.name)}")
		if self.image is not None and not isinstance(self.image, str):
			raise TypeError(f"Expected 'image' to be of type {str}, but got {type(self.image)}")
