from otupy.types.base import Choice
from otupy.types.data.hostname import  Hostname
from otupy.types.data.ipv4_addr import IPv4Addr
from otupy.core.register import Register


class Server(Choice):
	""" Generic computing environment

		A Server is a generic computing environment (no cloud).
		Probably not used.

		It can be identified by either its hostname or IPv4 address.
	"""

    #hostname: hostname of the server
	#ipv4_addr: 32 bit IPv4 address as defined in [RFC0791]

	register = Register({'hostname': Hostname, 'ipv4_addr': IPv4Addr})

