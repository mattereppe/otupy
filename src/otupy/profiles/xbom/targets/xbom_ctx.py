from otupy import ArrayOf, target

from otupy.profiles.xbom.profile import Profile


@target(name='boms', nsid=Profile.nsid)
class XbomTarget(ArrayOf(str)):
	""" Xbom-ctx
		
		The Xbom target is used to request Bills of Materials. 
		This target may include a list of component identifiers.
		If no identifier is provided, all BOMs are returned.
		Otherwise, only the BOMs of the specified components are returned.

		This target is currently only used with the query action to return the BOMs.
		In the future, the profile may be extended to use both the ``query`` and ``scan``
		actions. The former will ask for the list of components, the latter will ask
		to build and return the BOM of one or more components.
	
	"""
	pass
	
