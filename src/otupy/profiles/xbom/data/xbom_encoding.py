from otupy import Enumerated

class XbomEncoding(Enumerated):
	"""Xbom serialization format
	
		Defines a list of serialization formats for converting BOM objects to strings.
		Every BOM standards will likely support only a subset of  serialization formats.
	"""
	
	json = 0
	xml = 1
	yaml = 2
