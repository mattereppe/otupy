import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.targets.sbom_ctx import SbomCtx


# Context is deprecated - use SbomCtx with 'sbom' target instead
# Keeping this as an alias for backward compatibility but not registering as a target
class Context(SbomCtx):
	""" Context (DEPRECATED)

		DEPRECATED: Use SbomCtx with the 'sbom' target name instead.
		
		This class is kept for backward compatibility but is no longer registered
		as a target. The 'sbom' target (SbomCtx) should be used for XBOM discovery.
		
		:param format: Specifies the format of the SBOM (e.g. CycloneDX). Defaults to CycloneDX if not specified.
		:param names: A list of specific names used to identify components or services to filter.
	"""
	pass
