""" Network firewall

	Defines the main characteristics of an IP firewall.
"""

from otupy import Map

class Firewall(Map):
	""" Firewall

		This is only a placeholder to automatically generate valid subtypes for SIds.
		
	"""
	fieldtypes = dict(routes= str)
	""" Field types
	
		This is the definition of the routing table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"Firewall()"

