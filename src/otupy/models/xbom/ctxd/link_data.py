from otupy import Record
from otupy.models.ctxd import Link, Consumer

class LinkData(Record):
	""" Link record

		A ctxd Link together with its origin (consumer that provided it).
	"""
	consumer: Consumer = None
	link: Link = None

	def __init__(self, linkdata: object = None, link: Link = None, consumer=None):
		""" Initialize for an existing LinkData or Link/Consumer pair """
		if linkdata:
			self.link = linkdata.link
			self.consumer = linkdata.consumer
		else:
			if not link or not consumer:
				raise TypeError("LinkData must include both consumer and link")
			self.link = link
			self.consumer = consumer

	def __repr__(self):
		return f"LinkData(link={self.link}, consumer={self.consumer})"

	def __str__(self):
		return self.__repr__()

		
