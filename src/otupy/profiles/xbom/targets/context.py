import otupy as oc2

from otupy.profiles.xbom.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.xbom.data.name import Name
from otupy.core.target import target

@oc2.target(name='context', nsid=Profile.nsid)
class Context(oc2.types.base.Record):
	""" Context

		It describes the service environment, its connections and security capabilities.
	"""
	boms: ArrayOf(Name) = None  # type: ignore
	""" List the bom names that the command refers to """

	def __init__(self, boms: list[Name] | None = None):
		self.boms = ArrayOf(Name)(boms) if boms is not None else None

	def __repr__(self):
		return f"Context(services={self.services}, links={self.links})"

	def __str__(self):
		return f"Context(services={self.services}, links={self.links})"
