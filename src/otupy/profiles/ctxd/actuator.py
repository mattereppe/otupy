""" Context Discovery profile

	This modules contains the definition of the `ctxd` profile. It is mostly used as a container
	for the namespace identifier.
"""
import otupy as oc2

from otupy.profiles.ctxd.profile import Profile

@oc2.actuator(nsid=Profile.nsid)
class Specifiers(oc2.Map):
	""" CTXD Specifiers
	
		Define the set of specifiers defined in this specification that are meaningful in the context of CTXD.
		It implements the data structure define in the section "Actuator Specifiers"
	"""
	fieldtypes = dict(domain=str, asset_id=str)
	
	def __init__(self, dic):
		""" Initialize the `Actuator` profile

			The profile can be initialized by passing the internal fields explicitely 
			(i.e., by giving them as ``key=value`` pair.

			:param dic: A list of ``key=value`` pair which allowed values are given
				by `fieldtype`.
		"""
		self.nsid = Profile.nsid
		oc2.Map.__init__(self, dic)

	def __eq__(self, other):
		""" The comparison operator

			Return true if two specifiers are equal.
		"""
		for k,v in self.items():
			if k not in other:
				return False
			# else: k is in other
			if v != other[k]:
				return False
		return True

	
	def __str__(self):
		id = self.nsid + '('
		for k,v in self.items():
			id += str(k) + ':' + str(v) + ','
		id = id.strip(',')
		id += ')'
		return id

