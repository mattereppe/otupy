""" XML Encoding

	This module provides the code for encoding OpenC2 messages with XML.
	XML encoding is mostly provided to demonstrate the meta-serialization
	format, since there is no official documentation from OASIS about
	this format.
"""
import xmltodict

from otupy import Encoder, register_encoder


@register_encoder
class XMLEncoder(Encoder):
	""" XML Encoder
	
		This class implements the `Encoder` interface for the XML format. It leverages
		the intermediary dictionary representation.

		The `XMLEncoder` can be used to create an OpenC2 stack in `Consumer` and `Producer`.
	"""
	encoder_type = 'xml'
	""" The label that is used to identify this `Encoder` in OpenC2 messages. """
	OpenC2Root = 'OpenC2Msg'
	""" The root of the XML message. """

	@staticmethod
	def encode(obj):
		""" Encode an OpenC2 object

			This method is used to encode an OpenC2 object, which usually is a `Command` or `Message`. 
			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy classes. Attribute types are not used.

			Since XML strictly requires a single root, additional nesting of the the OpenC2 message
			is necessary. The message is arbitrary enclosed in an object.

			:param obj: A valid otupy object.
			:return: A string with the xml representation of the `obj`.

		"""
		def _preprocessor(d):
			"Workaround for unmanaged cases"

			# Empty lists suppress the key
			for k, v in d.items():
				try:
					v = _preprocessor(v)
				except AttributeError:
					if not v:
						d[k] = None
				
			return d


		obj = _preprocessor(Encoder.todict(obj))
		return xmltodict.unparse({XMLEncoder.OpenC2Root: obj}, pretty=True)

	@staticmethod
	def decode(msg, msgtype=None):
		""" Decode an OpenC2 message

			This method is used to create an otupy object of type `msgtype` from a xml record. 
			The otupy class `msgtype` corresponding to the xml record `msg` must be explicitly provided,
			since parsing and automatically inferring the `msgtype` is not currently implemented.

			The implementation leverages the intermediary dictionary representation and it is
			therefore agnostic of otupy classes. Note that the real OpenC2 message is wrapped in an 
			additional object to satisfy XML syntax requirements (see encode()).

			:param msg: The xml record to decode.
			:param msgtype: The otupy class to convert the xml to.
			:return: An `msgtype` class initialized according to the xml content.
		"""

		""" This function ensures int numbers are returned as such. Otherwise, they are returned
			as strings and this make the deconding of EnumeratedID fail.
		"""
		def _postprocessor(path, key, value):
			try:
				return key , int(value)
			except (ValueError, TypeError):
				return key, value

		if msgtype == None:
			return xmltodict.parse(msg, postprocessor=_postprocessor)[XMLEncoder.OpenC2Root]

		if isinstance(msg, str):
			return Encoder.decode(msgtype, xmltodict.parse(msg, postprocessor=_postprocessor)[XMLEncoder.OpenC2Root])
		else:
			return Encoder.decode(msgtype, msg)

