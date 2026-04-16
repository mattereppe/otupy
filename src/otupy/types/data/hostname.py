import fqdn

class Hostname:
	""" A hostname that can be used to connect to this device over a network """
		
	def __init__(self, hostname):
		self.set(str(hostname))

	def set(self, hostname):
		""" Check hostname fullfils RFC 1123 requirements """
		if fqdn.FQDN(str(hostname), min_labels=1).is_valid:
			self._hostname = str(hostname)
		else:
			raise ValueError("Invalid hostname -- not compliant to RFC 1123")

	def get(self):
		""" Returns the hostname as string """
		return self._hostname

	def __str__(self):
		return self._hostname

	def __repr__(self):
		return self._hostname

	def __hash__(self):
		return hash(self._hostname)

	def __eq__(self, other):
		if other is None:
			return False
		# Support comparison with strings
		if isinstance(other, str):
			return self._hostname == other
		# Support comparison with other Hostname objects
		if hasattr(other, '_hostname'):
			return self._hostname == other._hostname
		return False
