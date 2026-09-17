from otupy import Enumerated

class XbomFormat(Enumerated):
	""" Xbom data model
	
		Defines possible data models to represent the BOM. Even if most of data models are
		expected to be defined by international standards, it is also possible to define
		experimental and proprietary data models.
	"""
	
	ctxd = 0
	""" Otupy native data model for context discovery. """
	cyclonedx = 1
	""" The CycloneDX standard for application security contexts and supply chain component analysis. """
