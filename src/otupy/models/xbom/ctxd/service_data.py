from otupy import Record
from otupy.models.ctxd import Service, Consumer

class ServiceData(Record):
	""" Service record

		A ctxd service together with its origin (consumer that provided it).
	"""
	consumer: Consumer = None
	service: Service = None

	def __init__(self, servicedata: object = None, service: Service = None, consumer=None):
		""" Initialize for an existing ServiceData or Service/Consumer pair """
		if servicedata:
			self.service = servicedata.service
			self.consumer = servicedata.consumer
		else:
			if not service or not consumer:
				raise TypeError("ServiceData must include both consumer and service")
			self.service = service
			self.consumer = consumer

	def __repr__(self):
		return f"ServiceData(service={self.service}, consumer={self.consumer})"

	def __str__(self):
		return self.__repr__()

		
