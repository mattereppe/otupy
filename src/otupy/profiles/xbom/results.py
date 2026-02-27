""" XBOM Response extensions

"""
import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.data.xbom import Xbom

@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
	""" XBOM Results

		Extensions to the base class `otupy.core.response.Results`.
		 
		[Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

	"""
	fieldtypes = {'bom': Xbom}
