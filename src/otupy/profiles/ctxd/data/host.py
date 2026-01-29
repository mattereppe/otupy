from otupy.profiles.ctxd.data.network_node import NetworkNode

class Host(NetworkNode):
	""" Generic Host

		A Host is an electronic device designed to run a general-purpose operating system and application software.
		This abstraction specifically focuses on network hosts, namely devices attached to networks. For this reason,
		it extends the basic model of `NetworkNode` with additional details about the hardware and attached peripherals
		(still to be implemented).

		A Host will typically contain a computing environment (`Computer`); it could also be virtualized, giving rise
		to the `VM` model.

		For now, there are no custom attributes for the Host. It is mostly conceived to distinguish between different 
		node types.

	"""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	
	def __repr__(self):
		return (f"Host({super().__repr__()})")
	
	def __str__(self):
		return __repr__(self)

