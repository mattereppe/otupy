from otupy import Record
from otupy.models.ctxd import Link, Consumer

class LinkData(Record):
	""" Link record

		A ctxd Link together with its source (consumer that provided it).
	"""
	source: Consumer = None
	link: Link = None

	def __init__(self, linkdata: object = None, link: Link = None, source: Consumer=None):
		""" Initialize for an existing LinkData or Link/Consumer pair """
		if linkdata:
			self.link = linkdata.link
			self.source = linkdata.source
		else:
			if not link or not source:
				raise TypeError("LinkData must include both consumer and link")
			self.link = link
			self.source = source

	def __repr__(self):
		return f"LinkData(link={self.link}, source={self.source})"

	def __str__(self):
		return self.__repr__()

		
