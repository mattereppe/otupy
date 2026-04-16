from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record


class Server(Record):
	""" Physical server

		A ``Serveer`` is a true computing hardware, currently intended for any kind of high-end or low-end
		computer (namely, it includes laptops and desktops). This might be changed in the future with
		additional revisions and refinements of the model..
		It provides real hardware as network interfaces, virtual CPUs, virtual RAM, and storage.
		Since this model shares most of the components with any other network host, it will inherit from
		the `Host` abstraction and will extend with additional information. 
	"""

	def __init__(self, server=None):
		# Placeholder for future extensions
		if isinstance(server, Server):
			pass
		else:
			pass


	def __repr__(self):
		return f"Server()"
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert Server to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		properties = [
			Property(name="otupy:type", value="server")
		]
		
		return Component(
			name="server",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("server"),
			properties=properties
		)

