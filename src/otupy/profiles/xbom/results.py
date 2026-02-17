""" XBOM Response extensions

"""
import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.xbom.data.name import Name
# from otupy.profiles.xbom.data.service import Service
# from otupy.profiles.xbom.data.link import Link
from otupy.profiles.xbom.data.xbom import Xbom


@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
	""" XBOM Results

		Extensions to the base class `otupy.core.response.Results`.
		 
		[Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

	"""
	fieldtypes = {'bom': Xbom, 'bom_names': ArrayOf(Name)}
