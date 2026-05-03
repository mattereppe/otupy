from otupy.profiles.ctxd.profile import Profile 
from otupy import Record, ArrayOf, target
from otupy.models.ctxd import SId

@target(name='context', nsid=Profile.nsid)
class Context(Record):
	""" Context
		
    	This retrieves the ctxd format of the current Bill of Materials.
		References to specific services/links have been removed since links do
		not have their own `SId` and it is unlikely to discover specific `Services`
		with the related `Links`.
		Indeed, this approach is more similar to xBOM formats.

	"""
	pass
#	services: ArrayOf(SId) = None # type: ignore
#	""" List the service names that the command refers to """
#	links: ArrayOf(SId) = None # type: ignore
#	""" List the link names that the command refers to """
#
#
#
#	def __init__(self, services = None, links = None):
#		self.services = ArrayOf(SId)(services) if services is not None else None
#		self.links = ArrayOf(SId)(links) if links is not None else None
#
#
#	def __repr__(self):
#		return (f"Context(services={self.services}, links={self.links})")
#	
#	def __str__(self):
#		return f"Context(" \
#	            f"services={self.services}, " \
#	            f"links={self.links})"
