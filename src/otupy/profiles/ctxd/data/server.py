from otupy.profiles.ctxd.data.host import Host

class Server(Host):
	""" Physical server

		A ``Serveer`` is a true computing hardware, currently intended for any kind of high-end or low-end
		computer (namely, it includes laptops and desktops). This might be changed in the future with
		additional revisions and refinements of the model..
		It provides real hardware as network interfaces, virtual CPUs, virtual RAM, and storage.
		Since this model shares most of the components with any other network host, it will inherit from
		the `Host` abstraction and will extend with additional information. 
	"""

	def __init__(self, server=None,
			**kwargs):
		if(isinstance(server, Server)):
			super().__init__(server)
		else:
			super().__init__(**kwargs)

	def __repr__(self):
		return (f"Server("
					 f"{super().__repr__()},")
	
	def __str__(self):
		return self.__repr__()

