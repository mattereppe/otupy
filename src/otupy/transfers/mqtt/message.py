""" MQTT Message
	
	This module defines the MQTT definition of the abstract OpenC2 Message data.
	See Sec. 2.4.2 of the MQTT Specification. Note that the definition is not
	compliant with the examples in Appendix A. Since Appendix A is non-normative,
  	the current implementation is compliance with the definition in Sec. 2.4.2.
	An alternative implementation using the same serialization requirements as HTTP 
	(Appendix A) is also available (see message-http.py).
	
"""
import dataclasses
import logging
import copy

import otupy as oc2


OpenC2Contents = oc2.Register()
""" List allowed OpenC2-Content (see Sec. 3.3.2 of the Specification) """
OpenC2Contents.add('request', oc2.Command, 1)
OpenC2Contents.add('response', oc2.Response, 2)
# Section 2.4.2 also define a Notification placeholder,
# but there is not indication how to manage it.
# Since there is no indication about the data structure, this
# implementation does not include it.
# OpenC2Contents.add('notification', oc2.Notification, 3)

class OpenC2Content(oc2.Choice):
	""" MQTT Message OpenC2-Content (see Sec. 3.3.2 of the Specification) """
	register = OpenC2Contents

@dataclasses.dataclass
class Message(oc2.Record):
	""" MQTT Message representation

		This class implements the MQTT-specific representation of the 
		OpenC2 Message metadata. The OpenC2 Message metadata are described in 
		Table 3.1 of the Language Specification as message elements, but they are not
		framed in a concrete structure. The MQTT Specification defines such structure 
		in Sec. 2.4.2, and this class is its implementation. The MQTT specification 
		mandates the usage of the Message type defined in Table 3-1 of the Specification,
		but does not provide serialization requirements.

		The methods of this class are meant to translate back and for the otupy
		`Message` class.
	"""
	content: OpenC2Content = None
	""" Contains the `Content` """
	request_id: str = None
	""" Request identifier """
	created: oc2.DateTime = None
	""" Creation time """ 
	from_: str = None
	""" Sender of the message """
	to: oc2.ArrayOf(str) = None
	""" Receivers of the message """

	def set(self, msg: oc2.Message):
		""" Create MQTT `Message` from otupy `Message` 
			
			:param msg: An otupy `Message`.
			:return: An MQTT `Message`
		"""
		self.request_id = msg.request_id
		self.created = msg.created
		self.from_ = msg.from_
		self.to = msg.to

		self.content = OpenC2Content(msg.content)

		
	def get(self):
		""" Create an otupy `Message` from MQTT `Message` 
			
			:param msg: An otupy `Message`.
			:return: An HTTP `Message`
		"""
		msg = oc2.Message(self.content.getObj())
		msg.request_id = self.request_id 
		msg.created = self.created
		msg.from_ = self.from_
		msg.to = self.to
		msg.msg_type = msg.content.getType()

		return msg

	def todict(self, e):
		""" Fix dictionary representation

			Since "from" is a reserved Python keyword, we needed to use "from_" as variable name,
			which is not what is expected in the serialization. We therefore need to replace
			this.

			:param e: Encoder to be used for serialization
			:return: The serialization of the MQTT Message
		"""
		tmp = super().todict(e)
		if 'from_' in tmp:
			tmp['from']=tmp.pop['from_']

		return tmp

	@classmethod
	def fromdict(clstype, dic, e):
		""" Fix dictionary representation

			Same problem as for serialization, we need to convert the OpenC2 key "from" into
			the Python variable "from_".

			:param dic: The intermediary dictionary representation from which the object is built.
			:param e: The :py:class:`~otupy.core.encoder.Encoder` that is being used.
			:return: An instance of this class initialized from the dictionary values.
		"""
		if 'from' in dic:
			dic['from_']=dic.pop('from')

		return super().fromdict(dic, e)



