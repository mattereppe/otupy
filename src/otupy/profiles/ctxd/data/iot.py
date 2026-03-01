from otupy import  Record

class IoT(Record):
	"""IOT
    it is the description of the service - IOT

	"""
	type: str = None
	""" type of the IOT device"""


	def __init__(self, iot=None, type=None):
		if iot is not None:
			self.type = iot.type
		else:
			self.type = type 


	def __repr__(self):
		return (f"IoT("
	             "type={self.type})")
	
	def __str__(self):
		return self.__repr__()
	
