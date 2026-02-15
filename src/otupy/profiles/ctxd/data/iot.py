from otupy.profiles.ctxd.data.host import Host


class IOT(Host):
	"""IOT
    it is the description of the service - IOT

	"""
	type: str = None
	""" type of the IOT device"""


	def __init__(self, iot=None, type=None, **kwargs):
		if isinstance(iot, IOT):
			super().__init__(server)
			self.type = iot.type
		else:
			super().__init__(**kwargs)
			self.type = type 

	def __repr__(self):
		return (f"IoT("
					 f"{super().__repr__()},"
	             "type={self.type})")
	
	def __str__(self):
		return self.__repr__()
	
