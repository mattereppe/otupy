""" Network router

	Defines the main characteristics of an IP router.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

class Router(Map):
	""" Router

		A flexible container for routing configurations.
		To be implemented
	"""
	fieldtypes = dict(routes= str)
	""" Field types
	
		This is the definition of the routing table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"Router({self['routes']})"

