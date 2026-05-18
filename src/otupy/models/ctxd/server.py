from otupy import  Record

class Server(Record):
	""" Physical server

		A ``Server`` is a true computing hardware, currently intended for any kind of high-end or low-end
		computer (namely, it includes laptops and desktops). This might be changed in the future with
		additional revisions and refinements of the model..
		It provides real hardware as network interfaces, virtual CPUs, virtual RAM, and storage.
		Since this model shares most of the components with any other network host, it will inherit from
		the `Host` abstraction and will extend with additional information. 
	"""

	def __init__(self, server=None):
		# Placeholder for future extensions
		if server is not None:
			pass
		else:
			pass


	def __repr__(self):
		return f"Server()"
	
	def __str__(self):
		return self.__repr__()

