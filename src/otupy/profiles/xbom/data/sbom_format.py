from otupy.types.base import Enumerated

class SbomFormat(Enumerated):
	"""Sbom-Format
	
	Defines the allowable standards for the Sbom data.
	The CycloneDX standard for application security contexts and supply chain component analysis.
	"""
	
	cyclonedx = 1
	""" The CycloneDX standard for application security contexts and supply chain component analysis. """
