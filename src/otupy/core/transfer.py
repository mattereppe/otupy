""" Transfer protocol

	Interface that defines the basic behavior of the Transfer Protocols.
"""

class Transfer:
	""" Transfer protocol

		This is the base class for all implementation of Transfer protocols.
	"""

	def send(self, msg, encoder):
		""" Sends a Message

			Encodes, sends a message, and returns the response.

			Implementations of this method may return either a plain `Message` or a list of `Messages`; the latter
			option is expected for those implementation that support delivery to multiple Consumers. Each `Transfer`
			implmentation shall use either options consistently (e.g., it should always return either a plain object or
			a list of objects).
			Callers of this method must be prepared to manage the two cases, by leveraging the knowledge of the `Transfer`
			implementation they are using. 
			In any case, implementations must guarantee the uniqueness of returned Messages (i.e., duplicates must
			be discarded by the Transfer protocol). 

			:arg msg: an otupy `Message` to send
			:arg encoder: the `Encoder` to be used 
			:return: An otupy `Message` or a list of `Message`s that contains the `Response`(s) to the sent `Command`.
		"""
		pass

	def receive(self, callback, encoder):
		""" Receives a Message
			
			Listen for incoming `Message`s and dispatches them to the `Actuator`. This method may
			be blocking or non-blocking. 
			
			The expected signature for the `callback` function:
				`callback(cmd: otupy.Message)`

			:arg callback: the `Consumer.dispatch` function that contains the logic to dispatch a `Message`
				to one or more `Actuator`
			:arg encode: the default `Encoder` instance to encode/decode Messages. Implementations might
				use the information carried within OpenC2 Messages to derive the `Encoder` instance 
				(retrieved from the `Encoders` variable.
			:return: None
		"""
		pass
