""" XBOM Response extensions

"""
import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.xbom_encoding import XbomEncoding

@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
	""" XBOM Results

		Extensions to the base class `otupy.core.response.Results`.
		 
		[Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

		:param boms: An array of boms, serialized according to the specific format.
		:param format: The data model used to represent the xbom.
		:param encoding: The serialization format used to encode the object into a string.
	"""
	fieldtypes = {'boms': oc2.ArrayOf(str), 'format': XbomFormat, 'encoding': XbomEncoding}
