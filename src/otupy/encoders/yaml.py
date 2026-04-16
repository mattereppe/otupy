""" YAML Encoding

	This module provides the code for encoding OpenC2 messages with YAML.
	YAML encoding is mostly provided to demonstrate the meta-serialization
	format, since there is no official documentation from OASIS about
	this format.

	This implementation is based on PyYAML, which uses YAML 1.1. Be aware that 
	YAML 1.1 considers "on"/"off" and their capitalized versions as boolean values,
	so they are implicitely converted to True/False when parsing. This means that
	"on"/"off" must be explicitly enclosed in tics to be interpreted as strings
	in OpenC2 messages.
"""
import yaml

from otupy import Encoder, register_encoder


@register_encoder
class YAMLEncoder(Encoder):
	""" YAML Encoder
	
		This class implements the `Encoder` interface for the YAML format. It leverages
		the intermediary dictionary representation.

		The `YAMLEncoder` can be used to create an OpenC2 stack in `Consumer` and `Producer`.
	"""
	encoder_type = 'yaml'
	""" The label that is used to identify this `Encoder` in OpenC2 messages. """

	@staticmethod
	def encode(obj):
		""" Encode an OpenC2 object

			This method is used to encode an OpenC2 object, which usually is a `Command` or `Message`. 
			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy classes.

			:param obj: A valid otupy object.
			:return: A string with the yaml representation of the `obj`.

		"""
		return yaml.dump(Encoder.todict(obj))

	@staticmethod
	def decode(msg, msgtype=None):
		""" Decode an OpenC2 message

			This method is used to create an otupy object of type `msgtype` from a yaml record. 
			The otupy class `msgtype` corresponding to the yaml record `msg` must be explicitly provided,
			since parsing and automatically inferring the `msgtype` is not currently implemented.

			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy classes.

			:param msg: The yaml record to decode.
			:param msgtype: The otupy class to convert the yaml to.
			:return: An `msgtype` class initialized according to the yaml content.
		"""
		if msgtype == None:
			return yaml.safe_load(msg)

		if isinstance(msg, str):
			return Encoder.decode(msgtype, yaml.safe_load(msg))
		else:
			return Encoder.decode(msgtype, msg)

