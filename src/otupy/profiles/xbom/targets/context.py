import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.targets.xbom_ctx import XbomCtx as XbomCtx


# Context is deprecated - use XbomCtx with 'xbom' target instead
# Keeping this as an alias for backward compatibility but not registering as a target
class Context(XbomCtx):
	""" Context (DEPRECATED)

		DEPRECATED: Use XbomCtx with the 'xbom' target name instead.
		
		This class is kept for backward compatibility but is no longer registered
		as a target. The 'xbom' target (XbomCtx) should be used for XBOM discovery.
		
		:param format: Specifies the format of the XBOM (e.g. CycloneDX). Defaults to CycloneDX if not specified.
		:param names: A list of specific names used to identify components or services to filter.
	"""
	pass