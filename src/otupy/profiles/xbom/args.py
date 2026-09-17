""" XBOM Arguments
	
	This module extends the Args defined by the Language Specification.
"""
import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.xbom_encoding import XbomEncoding


@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
	""" XBOM Args

		:param format: Requests the format to represent the XBOM (e.g. ctxd, CycloneDX). 
		:param encoding: Requests the serialization format for the XBOM (e.g., json, xml). Must be supported by the requested format (if any).
		:param cached: Set to True to speed up the answer by returning cached results, False (default) to update services before returning the response.

	"""
	fieldtypes = {'format': XbomFormat, 'encoding': XbomEncoding, 'cached': bool}
