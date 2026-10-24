from otupy import Record
from otupy.models.ctxd import Service, Consumer

class ServiceData(Record):
	""" Service record

		A ctxd service together with its source (consumer that provided it).
	"""
	source: Consumer = None
	service: Service = None

	def __init__(self, servicedata: object = None, service: Service = None, source: Consumer=None):
		""" Initialize for an existing ServiceData or Service/Consumer pair """
		if servicedata:
			self.service = servicedata.service
			self.source = servicedata.source
		else:
			if not service or not source:
				raise TypeError("ServiceData must include both consumer and service")
			self.service = service
			self.source = source

	def __repr__(self):
		return f"ServiceData(service={self.service}, source={self.source})"

	def __str__(self):
		return self.__repr__()

		
