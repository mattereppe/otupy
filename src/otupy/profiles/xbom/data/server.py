from otupy.types.base import Choice
from otupy.types.data.hostname import  Hostname
from otupy.types.data.ipv4_addr import IPv4Addr
from otupy.core.register import Register
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType


class Server(Choice):
	""" Generic computing environment

		A Server is a generic computing environment (no cloud).
		Probably not used.

		It can be identified by either its hostname or IPv4 address.
	"""

    #hostname: hostname of the server
	#ipv4_addr: 32 bit IPv4 address as defined in [RFC0791]

	register = Register({'hostname': Hostname, 'ipv4_addr': IPv4Addr})

	def as_cyclonedx(self) -> Component:
		"""Convert Server to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type PLATFORM.
		"""
		properties = [
			Property(name="otupy:type", value="server")
		]
		
		# Get the current choice value
		choice_key, choice_value = self.getObj()
		name = "unknown"
		
		if choice_key == 'hostname':
			name = str(choice_value)
		elif choice_key == 'ipv4_addr':
			name = str(choice_value)
			properties.append(Property(name="otupy:server:ipv4-addr", value=str(choice_value)))
		
		return Component(
			name=name,
			type=ComponentType.PLATFORM,
			properties=properties
		)

