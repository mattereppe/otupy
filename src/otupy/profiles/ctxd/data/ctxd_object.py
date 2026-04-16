from otupy.types.base import Record

class CTXDObject(Record):
	""" Common fields to all CTXD model objects """

	name: str = None
	""" A name for this node (e.g., network namespace name) """
	id: str = None
	""" ID of the node, preferably globally unique """
	description: str = None
	""" Generic description of the node (including its role) """

	def __init__(self, 
			name:str = None, 
			id:str = None, 
			description:str = None): 
	
		self.name = name if name is not None else None
		self.id = id if id is not None else None
		self.description = description if description is not None else None

	def __repr__(self):
		return (
	            f"name='{self.name}',"
					f"id={self.id}, "
					f"description='{self.description}'," 
				)
	
	def __str__(self):
		return self.__repr__()

