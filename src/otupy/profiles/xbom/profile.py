""" Context Discovery namespace

	This module defines the nsid and unique name for the XBOM profile.
	No explicit values are used anywhere in the rest of the code.
"""

import otupy as oc2

nsid = 'x-xbom' # Prefix 'x-' is required

@oc2.extension(nsid = nsid)
class Profile(oc2.Profile):
	""" XBOM Profile

		Defines the namespace identifier and the name of the SLPF Profile.
	"""
	nsid = nsid
	name = 'x Bill of Materials'
