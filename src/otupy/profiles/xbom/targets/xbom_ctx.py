import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.xbom.data.xbom_format import XbomFormat


@oc2.target(name='xbom', nsid=Profile.nsid)
class XbomCtx(oc2.Map):
	""" Xbom-ctx
		
	The Xbom type defines the arguments used to identify or format a Software Bill of Materials.
	
	:param format: Specifies the format of the XBOM (e.g. CycloneDX). Defaults to CycloneDX if not specified.
	:param names: A list of specific names used to identify components or services.
	"""
	fieldtypes = {'format': XbomFormat}
	
	def __init__(self, dic=None, **kwargs):
		""" Initialize the Xbom-ctx target
		
		The target can be initialized by passing a dictionary or keyword arguments.
		
		:param dic: A dictionary with 'format' and/or 'names' fields
		:param kwargs: Keyword arguments for 'format' and/or 'names'
		"""
		if dic is None:
			dic = kwargs
		oc2.Map.__init__(self, dic)
	
	def __repr__(self):
		return f"XbomCtx(format={self.get('format')})"
	
	def __str__(self):
		return f"XbomCtx(format={self.get('format')})"
