from otupy.types.base import Enumerated

class XbomFormat(Enumerated):
	"""Xbom-Format
	
	Defines the allowable standards for the Xbom data.
	The CycloneDX standard for application security contexts and supply chain component analysis.
	"""
	
	cyclonedx = 1
	""" The CycloneDX standard for application security contexts and supply chain component analysis. """
