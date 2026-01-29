from otupy.types.base import Record, ArrayOf
from otupy.profiles.ctxd.data.port import Port

class VM(Record):
	"""VM
    it is the description of the service - Virtual Machine
	"""
	description: str = None
	""" Generic description of the VM """
	id: str = None
	""" ID of the VM """
	name: str = None
	""" Name of the VM"""
	ports: ArrayOf(Port) = None
	""" Network interfaces of the VM"""
	image: str = None
	""" Software image loaded in the VM """

	def __init__(self, description:str = None, id:str = None, name:str = None, image:str = None, ports:ArrayOf(Port) = None):
		if(isinstance(description, VM)):
			self.description = description.description
			self.id = description.id
			self.name = description.name
			self.image = description.image
			self.ports = description.ports
		else:
			self.description = description if description is not None else None
			self.id = id if id is not None else None
			self.name = name if name is not None else None
			self.image = image if image is not None else None
			if ports is not None:
				self.ports = ArrayOf(Port)()
				for port in ports:
					if isinstance(port, dict):
						self.ports.append(Port(**port))
					else:
						self.ports.append(Port(port))
			else:
				self.ports = None
		self.validate_fields()

	def __repr__(self):
		return (f"VM(description='{self.description}', id={self.id}, "
	             f"name='{self.name}', image={self.image}, ports={self.ports})")
	
	def __str__(self):
		return f"VM(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"name={self.name}, " \
	            f"image={self.image}, " \
					f"ports={self.ports})" 

	def validate_fields(self):
		if self.description is not None and not (isinstance(self.description, str) or isinstance(self.description, VM)):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.id is not None and not isinstance(self.id, str):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.name is not None and not isinstance(self.name, str):
			raise TypeError(f"Expected 'name' to be of type str, but got {type(self.name)}")
		if self.image is not None and not isinstance(self.image, str):
			raise TypeError(f"Expected 'image' to be of type {str}, but got {type(self.image)}")
		if self.ports is not None and not issubclass(type(self.ports), list):
			raise TypeError(f"Expected 'ports' to be of type {ArrayOf(Port)}, but got {type(self.ports)}")	
