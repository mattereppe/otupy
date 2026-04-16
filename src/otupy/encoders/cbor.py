""" CBOR Encoding

	This module provides the code for encoding OpenC2 messages with CBOR.
"""
import cbor2

from otupy import Encoder, register_encoder


@register_encoder
class CBOREncoder(Encoder):
	""" CBOR Encoder
	
		This class implements the `Encoder` interface for the CBOR format. It leverages
		the intermediary dictionary representation.

		The `CBOREncoder` can be used to create an OpenC2 stack in `Consumer` and `Producer`.
	"""
	encoder_type = 'cbor'
	""" The label that is used to identify this `Encoder` in OpenC2 messages. """
	is_binary = True
	""" This notifies the transfer protocol that special processing may be needed. """

	@staticmethod
	def encode(obj):
		""" Encode an OpenC2 object

			This method is used to encode an otupy object, which usually is a `Command` or `Message`. 
			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy clases.

			:param obj: A valid otupy object.
			:return: A string with the cbor representation of the `obj`.

		"""
		return cbor2.dumps(Encoder.todict(obj))

	@staticmethod
	def decode(msg, msgtype=None):
		""" Decode an OpenC2 message

			This method is used to create an otupy object of type `msgtype` from a cbor record. 
			The otupy class `msgtype` corresponding to the cbor record `msg` must be explicitly provided,
			since parsing and automatically inferring the `msgtype` is not currently implemented.

			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy classes.

			:param msg: The cbor record to decode.
			:param msgtype: The otupy class to convert the cbor to.
			:return: An `msgtype` class initialized according to the cbor content.
		"""
		if msgtype == None:
			return cbor2.loads(msg)

		if isinstance(msg, bytes):
			return Encoder.decode(msgtype, cbor2.loads(msg))
		elif isinstance(msg,str):
			return Encoder.decode(msgtype, msg)
		else:
			raise ValueError("Unable to process cbor data type: "+type(msg))

