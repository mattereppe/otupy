""" Network bridge

	Defines the main characteristics of an Ethernet bridge/switch
"""

from otupy import Map, ArrayOf
from otupy.models.ctxd.network_interface import NetworkInterface

class Bridge(Map):
	""" Bridge

		A flexible container for network switches/bridges.
		To be implemented
	"""
	fieldtypes = dict(table= str, ifaces=ArrayOf(NetworkInterface) )
	""" Field types
	
		This is the definition of the bridge switching table. It must be defined by defining the structure
		of each entry.
	"""

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f"Bridge({self['table'] if 'table' in self else None})"

