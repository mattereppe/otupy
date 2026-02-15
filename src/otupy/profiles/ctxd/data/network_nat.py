""" Network Address Translation

	Defines the main characteristics of a NAT.
"""

from otupy import Map, ArrayOf, IPv4Net, IPv6Net

class NAT(Map):
	""" Router

		A flexible container for routing configurations.
		To be implemented
	"""
	fieldtypes = dict(rules= ArrayOf(str))
	""" Field types
	
		This is the definition of the translation table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"NAT({self['rules']})"

