""" CTXD Arguments
	
	This module extends the Args defined by the Language Specification
	(see Sec. 'Command Arguments Unique to CTXD').
"""
import otupy as oc2

from otupy.profiles.ctxd.profile import Profile


@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
	""" CTXD Args

		This class extends the Args defined in the Language Specification.
		The extension mechanism is described in the 
		[Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

		:param name_only: Set to True to get only service name, False (default) to get full details.
		:param cached: Set to True to speed up the answer by returning cached results, False (default) to update services before returning the response.

	"""
	fieldtypes = {'name_only': bool, 'cached': bool}

