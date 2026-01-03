""" MQTT Transfer Protocol

	This module defines implementation of the :py:class:`~otupy.core.transfer.Transfer` interface for the 
  	MQTT/MQTTS protocols. This implementation is mostly provided for 
	research and development purposes, but it is not suitable for production
	environments.

	The implementation follows the Specification for Transfer of the 
	Specification for Transfer of OpenC2 Messages via MQTT Version 1.0,
	which is indicated as the "Specification" in the following.
"""
import dataclasses
import requests
import logging
import copy
import aenum
import random
import time
import threading
import datetime

from paho.mqtt import client as mqtt_client

import otupy as oc2
from otupy.transfers.mqtt.message import Message
from otupy.core.version import _OPENC2_VERSION
from otupy.encoders.json import JSONEncoder

class UnsupportedMediaType(Exception):
	"""Exception raised for custom error scenarios.

		Attributes:

		    message -- explanation of the error
	"""
	
	def __init__(self, message):
	    self.message = message
	    super().__init__(self.message)

logger = logging.getLogger(__name__)
""" The logging facility in otupy """

# Definition of OpenC2 topics according to Sec. 2.2
MQTT_OC2_ALL_CMD_TOPIC = "oc2/cmd/all"
MQTT_OC2_AP_CMD_TOPIC = "oc2/cmd/ap/"
MQTT_OC2_DEVICE_CMD_TOPIC = "oc2/cmd/device/"
MQTT_OC2_ALL_RSP_TOPIC = "oc2/rsp"
MQTT_OC2_DEVICE_RSP_TOPIC = "oc2/rsp/device/"

# Connect options as defined in Sec. 3.1.1 (Connect)
MQTT_CLEANSTART=False

# Subscribe options as defined in Sec. 2.3 (Subscription options)
MQTT_MAXQOS=2
MQTT_NOLOCAL=True
MQTT_RETAINASPUBLISHED=True
MQTT_RETAINHANDLING=mqtt_client.SubscribeOptions.RETAIN_SEND_ON_SUBSCRIBE

# Session parameters
MQTT_SESSIONEXPIRYINTERVAL=60  # <= 300s (Sec. 3.1.1)
MQTT_MESSAGEEXPIRYINTERVAL=10 # Short message timeout because commands must be in nearly real-time

# Publish option as per Sec. 3.1.3
MQTT_PUBLISH_QOS=1 # Chosen by the implementation
MQTT_PUBLISH_RETAIN=False
MQTT_PUBLISH_CONTENTTYPE="application/openc2"
MQTT_PUBLISH_OC2REQUEST="req"
MQTT_PUBLISH_OC2RESPONSE="rsp"
MQTT_PUBLISH_OC2NOTIFICATION="ntf" # Unsupported
MQTT_PUBLISH_USERPROPERTY_MSGTYPE="msgType"
MQTT_PUBLISH_USERPROPERTY_ENCODING="encoding"

class OpenC2Role(aenum.enum):
	Consumer = 1
	Producer = 2

@oc2.transfer("mqtt")
class MQTTTransfer(oc2.Transfer):
	""" MQTT Transfer Protocol

		This class provides an implementation of the Specification. It builds on the paho library.

		Use `MQTTTransfer` to build OpenC2 communication stacks in `Producer` and `Consumer`.
	"""

	class MQTTUserData:
		""" Define the data structure to exchange data with MQTT thread

			It will include 
			- a list of (received) messages
			- the number of expected messages
			- an event to signal all expected messages were received
		"""
		event: threading.Event
		msg_queue: list
		expected_msgs: int

		def __init__(self, event: threading.Event, expected_msgs: int = None):
			""" Initialize MQTTUserData """
			self.msg_queue = list()
			self.event = event
			self.expected_msgs = expected_msgs
		


	def __init__(self, broker, port = 1883, role = OpenC2Role.Consumer, profiles = None, device_id = None, 
					username=None, password=None, client_id=None, response_timeout=10, usessl=False):
		""" Builds the `MQTTTransfer` instance

			The `broker` and `port` parameters are used to select theh MQTT Broker.
			This implementation only supports TCP as transport protocol.

			The topics to be subscribed or used for publishing will be automatically derived.
			If no `device_id` is provided, the device-specific topic will not be subscribed.
			The Specification does not cover the generation of device identifiers (Sec. 2.2); additionally,
			it is not clear why the Consumer's topic is denoted as `device_id` while the Producer's topic as
			`producer_id`. This implementation uses the same identifiers already present in the `Message` metadata
			(namely, `From` and `To` fields) (Sec. 2.4.2). Note that both Consumers and Producers are expected to
			*always* include their identifiers in the `From` field (Sec. 2.4.2), so this argument is mandatory
			for the MQTT transfer.

			According to Sec. 3.1.8:
			- Consumer SHALL subscribe to topics for all actuator devices, all-commands topic, individual topic for device
			- Producer SHALL subscribe to the general response topic
			- Producer SHOULD subscribe to their individual topic
			Therefore, 
			1) the `profiles` and `device_id` arguments are mandatory for Consumers;
			2) the `device_id` could be optional for Producers, but it is mandatory in this implementation because of the above requirement on the `From` field.
			This implementation will always subscribe all topics for Consumers/Producers.
			
			For sending data, the `send()` method will wait at most `response_timeout` secodns before returning. 
			In case the Commands are sent to specific devices, it will return as soon as all of them have answered.
			If the Command is broadcast to all APs or to all devices, it will return after the above timeout. The
			same will happen if the message is sent to specific devices, but they do not include their identifier in 
			the `Message.from` field, as required by the standard.

			For receiving data, the `receive()` method will keep MQTT message for at least `response_timeout`  seconds
			for detecting and discarding duplicates. Duplicates received after `response_timeout` seconds are not 
			guaranteed to be correctly detected as such.

			:param broker: Hostname or IP address of the MQTT Broker
			:param port: Transport port of the MQTT Broker
			:param device_id: OpenC2 device identifier to be used in topic name for the specific actuator (mandatory)
			:param profiles: list of profile names for actuators running on the Consumer (will be ignored by the Producer)
			:param username: Username to connect to MQTT broker
			:param password: Password to connect to MQTT broker
			:param client_id: Client identifier to connect to MQTT broker
			:param response_timeout: Timeout to wait for responses to commands from multiple devices (for Producers). 
			 							Timeout to detect duplicates of commands from multiple topics (for Consumers).
			:param usessl: Enable (`True`) or disable (`False`) SSL. Internal use only. Do not set this argument,
				use the `MQTTSTransfer` instead.
		"""
		self.broker = broker
		self.port = port
		self.username = username
		self.password = password
		self.role = role
		self.response_timeout = response_timeout

		self.mqtt_userdata = MQTTTransfer.MQTTUserData(threading.Event())

		# This implementation needs device_id to be inserted in the From field of OpenC2 Messages
		assert device_id is not None
		self.device_id = device_id

		# Make a few consistency checks
		if self.role == OpenC2Role.Consumer:
			assert profiles is not None
		  
		# Create the list of topics to subscribe, depending of the role played by the caller 
		# Mandatory topics (Sec. 3.1.8 of the Specification)
		subscribe_topics = []
		if self.role == OpenC2Role.Consumer:
			subscribe_topics.append(MQTT_OC2_ALL_CMD_TOPIC) 
			subscribe_topics.append(MQTT_OC2_DEVICE_CMD_TOPIC+device_id) 
			for p in profiles:
				subscribe_topics.append(MQTT_OC2_AP_CMD_TOPIC+p) 
		else:
			subscribe_topics.append(MQTT_OC2_ALL_RSP_TOPIC) 
			# Optional topic (Sec. 3.1.8 of the Specification)
			subscribe_topics.append(MQTT_OC2_DEVICE_RSP_TOPIC+device_id) 

		# Set parameters to connect to MQTT
		self.username=username
		self.password=password
		if not client_id:
			self.client_id = f'openc2client-{random.randint(0, 1000)}'
		else:
			self.client_id = client_id

		self.client=self._connect_mqtt()
		self.client.on_connect = self.on_connect
		self.client.on_subscribe=self.on_subscribe
		self.client.on_publish=self.on_publish
		self.client.on_message = self.on_message

		self.subscribed_topics = self._subscribe_mqtt_topic(subscribe_topics)
		logger.debug("Subscribed topics: %s\n", str(self.subscribed_topics))

	def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
		for rc in reason_code_list:
			logger.debug("SUBACK(%d): %s", mid, rc.getName())

	def on_connect(self, client, userdata, flags, rc, properties):
		logger.info("CONNACK: %s", rc.getName())

	def on_publish(self, client, userdata, mid, reason_code, properties):
			logger.debug("PUBACK(%d): %s", mid, reason_code.getName())

	def on_message(self, client, userdata, msg):
		""" Service callback on receiving data from MQTT subscribed topics """
		logger.debug("Received message %s from topic %s\n", self._mqttmsg_to_str(msg), msg.topic)

		if self.role == OpenC2Role.Consumer:
			self._on_message_cmd(client, userdata, msg)
		else: # TODO: implement the notification role
			self._on_message_rsp(client, userdata, msg)

	def _on_message_cmd(self, client, userdata, msg):
		""" Process a command at the consumer side """
		# Check whether this message was already processed
		# Also remove previous packets after response_timeout
		for c in userdata.msg_queue:
			if msg.payload in c:
				if  (datetime.datetime.now() - c[0]).seconds > self.response_timeout:
					userdata.msg_queue.remove(c)
				else:
					logger.info("Discarding duplicated Command")
					return
		userdata.msg_queue.append( (datetime.datetime.now(), msg.payload) )

		try:
			for p in msg.properties.UserProperty:
				if p[0] == MQTT_PUBLISH_USERPROPERTY_ENCODING:
					encname = p[1]
					break
		except:
			encname='json'
		
		try:
			cmd, encoder = self._recv(msg.properties, msg.payload)
			# TODO: Add the code to answer according to 'response_requested'
		except UnsupportedMediaType as e:
			# We were not able to understand the OpenC2 Message. 
			#	We must include "to" to be compliant; we'll use the client address.
			logger.warn("Unsupported MediaType: discarding request")
			content = oc2.Response(status=oc2.StatusCode.BADREQUEST, status_text=str(e))
			resp = oc2.Message(content)
			resp.content_type = oc2.Message.content_type
			resp.to = None # Consumers have no requirement to populate the "to" field
			resp.version = oc2.Message.version
			resp.encoder = encname
			encoder = oc2.Encoders[encname].value
			resp.status=oc2.StatusCode.BADREQUEST
		except oc2.EncoderError as e:
			logger.warn("Unable to understand the request: discarding")
			# TODO: Find better formatting (what should be returned if the request is not understood?)
			content = oc2.Response(status=oc2.StatusCode.BADREQUEST, status_text=str(e))
			resp = oc2.Message(content)
			resp.content_type = oc2.Message.content_type
			resp.version = oc2.Message.version
			resp.encoder = encname
			encoder = oc2.Encoders[encname].value
			resp.status=oc2.StatusCode.BADREQUEST 
			resp.to = None # WARNING: The following code catch any exception and may prevent debugging
		except Exception as e:
			# TODO: Find better formatting (what should be returned if the request is not understood?)
			logger.warn("Internal error: discarding request")
			content = oc2.Response(status=oc2.StatusCode.INTERNALERROR, status_text=str(e))
			resp = oc2.Message(content)
			resp.content_type = oc2.Message.content_type
			resp.version = oc2.Message.version
			resp.encoder = encname
			encoder = oc2.Encoders[encname]
			resp.status=oc2.StatusCode.INTERNALERROR
			resp.to = None
		else:
			logger.info("Processing command: %s", cmd)
			resp = self.message_processing_callback(cmd)

		logger.info("Got response: %s", resp)

		self._respond(resp, encoder)

	def _on_message_rsp(self, client, userdata, msg):
		""" Process a command at the consumer side """
		# No feedback to responses is possible, so if we don't understand the response, just
		# discard them

		logger.info("MQTT got response: %s", str(msg))
		try:
			rsp, encoder = self._recv(msg.properties, msg.payload)
		except Exception as e:
			logger.error("Unable to decode request: %s", msg.payload.decode("utf-8"))
		else:
			# Check whether the message was received from a subscribed topic or
			# it is addressed to this device (assuming in this case it was received
			# on the general topic /oc2/rsp
			if msg.topic in self.subscribed_topics or rsp.to == self.device_id:
				# Now check if the message is a duplicate
				# This implementation detects duplicates by comparing decoded messages
				# (since duplicates should have exactly the same payload, it seems safe
				# to assume they will be de-serialized exactly in the same way)	
				if not rsp in userdata.msg_queue:
					logger.info("Queuing response:\n%s", rsp)
					userdata.msg_queue.append(rsp)
					# If we know the number of expected messages, let's decrement it
					# and raise event if no more are expected
					if userdata.expected_msgs:
						userdata.expected_msgs-=1
						if userdata.expected_msgs <= 0:
							userdata.event.set()
							logger.debug("No more messages expected")
						else:
							logger.debug("Waiting for %d more messages", userdata.expected_msgs)
				else:
					logger.info("Duplicated message discarded")
			# else: the message was not addressed to this producer, silently discard it!
						

	def _connect_mqtt(self):
		# Set Connecting Client ID
		client = mqtt_client.Client(client_id=self.client_id, 
												callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2, 
												protocol=mqtt_client.MQTTv5,
												userdata=self.mqtt_userdata)
		logger.debug("Device %s connecting as MQTT client id: %s\n", self.device_id, self.client_id)

		# OpenC2 does not use Will message (Sec. 2.8)
		client.will_clear()
		# client.username_pw_set(username, password)
		client.username=self.username
		client.password=self.password
		# Connect properties 
		connect_properties = mqtt_client.Properties(mqtt_client.PacketTypes.CONNECT)
		connect_properties.SessionExpiryInterval = MQTT_SESSIONEXPIRYINTERVAL

		# Loop until connected to the broker
		# (no connection, no transfer!)
		ret = 1
		while ret != 0:
			ret = client.connect(self.broker, self.port, clean_start=MQTT_CLEANSTART,
						properties=connect_properties)
			if ret != 0:
				logger.warning("CONN: Unable to connect. Reason: %d", ret)
				logger.warning("Trying again...")
		return client

	def _get_mqtt_subscribe_options(self):
		# Set MQTT subscription options according to the specification
		#subscribe_properties = mqtt_client.Properties(mqtt_client.SUBSCRIBE)
		return mqtt_client.SubscribeOptions(qos=MQTT_MAXQOS, 
														noLocal=MQTT_NOLOCAL, 
														retainAsPublished=MQTT_RETAINASPUBLISHED, 
														retainHandling=MQTT_RETAINHANDLING)


	def _subscribe_mqtt_topic(self, topics):
		
		# Set MQTT subscription options according to the specification
		#subscribe_properties = mqtt_client.Properties(mqtt_client.SUBSCRIBE)
		subscribe_options = self._get_mqtt_subscribe_options()

		# Prepare the tuples of topics to subscribe
		topic_list = []
		try:
			for t in topics:
				topic_list.append( (t, subscribe_options) )
		except:
			topic_list.append((topics, subscribe_options))

		err, mid = self.client.subscribe(topic_list)
		if err == mqtt_client.MQTTErrorCode.MQTT_ERR_SUCCESS:
			logger.info("SUB(%d): Successfully subscribed to topic %s", mid, topics)
			return topics
		else:
			logger.error("SUB(%d): Unable to subscribe topic %s; Reason: %i", mid, topics, err)
			return None


	def _tomqtt(self, msg, encoder):
		""" Convert otupy `Message` to MQTT `Message` """
		m = Message()
		m.set(msg)

		# MQTT only accepts json and cbor serialization formats
		if not encoder.getName() in ['json', 'cbor']:
			raise Exception("Invalid serialization format for MQTT transfer!")

		# Encode the data
		if encoder is not None:
			data = encoder.encode(m)
		else:
			data = oc2.Encoder().encode(m)

		return data

	def _frommqtt(self, prop, data):
		""" Convert MQTT `Message` to otupy `Message` """

		# TODO: Check the MQTT  properties for version/encoding
		content_type =prop.ContentType
		if prop.PayloadFormatIndicator == 0x01:
			data_text = data.decode('utf-8')
		else:
			data_text = data
		data = data_text

		if not content_type.removeprefix('application/').startswith(oc2.Message.content_type):
			raise UnsupportedMediaType("Unsupported content type " + "content_type")

		for p in prop.UserProperty:
			if p[0] == MQTT_PUBLISH_USERPROPERTY_ENCODING:
				enctype = p[1]
				break
		try:
			encoder = oc2.Encoders[enctype].value
		except KeyError:
			raise UnsupportedMediaType("Unsupported encoding scheme: " + enctype)

		# HTTP processing to extract the headers
		# and the transport body
		msg = encoder.decode(data, Message).get()
		msg.content_type = content_type
		msg.version = _OPENC2_VERSION # Version is not carried in the metadata, this implementation assumes the version it can manage
		msg.encoding = encoder

		return msg, encoder

	def _send_mqtt_msg(self, publish_topics, msg, encoder):
		# The MQTT Transfer Specification requires the "from" field. Producers can use the "to" field, 
		# but this is not strictly required.
		# The Producer/Consumer implementation might not fill these fields, 
		# since they are not strictly required by the Language Specification.
		# This implementation always fills in the From field to be 
		# compliant with MQTT implementation.
		assert publish_topics is not None and publish_topics
		if msg.from_ is None:
			msg.from_ = self.device_id # device_id MUST be present (assertion-checked)

		# Convert the message to the specific MQTT representation
		openc2data = self._tomqtt(msg, encoder)
	
		# Set properties according to the Specification
		publish_properties = mqtt_client.Properties(mqtt_client.PacketTypes.PUBLISH)
		if (type(openc2data) == str):
			publish_properties.PayloadFormatIndicator = 0x01 # UTF-8 encoded character data
		else:
			publish_properties.PayloadFormatIndicator = 0x00 # unspecified byte stream
		publish_properties.MessageExpiryInterval = MQTT_MESSAGEEXPIRYINTERVAL
		publish_properties.ContentType = MQTT_PUBLISH_CONTENTTYPE
		match msg.msg_type:
			case oc2.MessageType.command:
				publish_properties.UserProperty = (MQTT_PUBLISH_USERPROPERTY_MSGTYPE, MQTT_PUBLISH_OC2REQUEST)
			case oc2.MessageType.response:
				publish_properties.UserProperty = (MQTT_PUBLISH_USERPROPERTY_MSGTYPE, MQTT_PUBLISH_OC2RESPONSE)
			case _:
				logger.error("Unmanaged message type: %s", msg.msg_type)
				logger.error("Skipping message")
				return None 
		publish_properties.UserProperty = ((MQTT_PUBLISH_USERPROPERTY_ENCODING, encoder.getName())) 	

		# Send the OpenC2 message and get the response
		logger.info("Sending message: %s\n", openc2data)

		for t in publish_topics:
			res = self.client.publish(t, openc2data, qos=MQTT_PUBLISH_QOS, 
												retain=MQTT_PUBLISH_RETAIN, properties=publish_properties)
#res.wait_for_publish(2) # Wait to know the status
			if res.rc == 0:
			    logger.info("PUB(%d): Message successfully published to topic %s", res.mid, t)
			else:
			    logger.warn("PUB(%d): Failed to publish message to topic %s", res.mid, t)



	# This function is used to send an MQTT message
	def send(self, msg, encoder):
		""" Sends OpenC2 message

			This method implements the required `Transfer` interface to send message to an OpenC2 server.
			Note that this method can be used by Producers only (it will fail if a Consumer invokes it)

			The MQTT specification does not dictate to which topic the messages are sent.
			This implementation follows a "polite" approach, which avoids flooding Consumers by publishing
			the messages over an unnecessary number of topics. The approach is to follow the filters the 
			`Producer` may have set on the message, by implementing the following logic:
			1. If msg.to is present, send the message to all devices in this field
			2. If msg.to is not present, send the message to the profile in the Command 
			3. If no profile is given, broadcast the message

			:param msg: The message to send (otupy `Message`).
			:param encoder: The encoder to use for encoding the `msg`.
			:return: An list of OpenC2  responses (`Response`).
		"""

		assert self.role == OpenC2Role.Producer

		publish_topics = []
		# We compute the number of expected responses as number of 
		# destinations in the "to" field; in case of broadcast to all
		# APs or all devices, we don't set a specific number.
		expected_responses = None
		# Implement the logic described in the inline documentation
		# Publish topics must be set at runtime, because we don't know the 
		# destination
		if msg.to is not None:
			for device in msg.to:
				publish_topics.append(MQTT_OC2_DEVICE_CMD_TOPIC+device)	
			expected_responses = len(msg.to)
		elif msg.content.actuator is not None:
			publish_topics.append(MQTT_OC2_AP_CMD_TOPIC+msg.content.actuator.getObj().nsid)
		else:
			publish_topics.append(MQTT_OC2_ALL_CMD_TOPIC)
		self.mqtt_userdata.expected_msgs = expected_responses
		logger.info("Publishing msg %s to topic %s\n", msg, publish_topics)

		self._send_mqtt_msg(publish_topics, msg, encoder)

		logger.info("Waiting for responses...")

		self.client.loop_start()
		try:
			self.mqtt_userdata.event.wait(timeout=self.response_timeout)	
		except KeyboardInterrupt:
			logger.warning("Interrupt signal received. There might be uncaught responses" )
		self.client.loop_stop()

		if self.mqtt_userdata.expected_msgs and self.mqtt_userdata.expected_msgs > 0:
			logger.warn("Missing responses: %d producers did not answer", self.mqtt_userdata.expected_msgs)

		return self.mqtt_userdata.msg_queue

	def _respond(self, msg, encoder):
		""" Responds to received OpenC2 message """

		# Send back to all-response topics and the producer-specific topic, 
		# if its device_id is available (it MUST be available, according to
		# the specification
# TODO: Use one topic only for responses.
# We currently use more topics for debugging purposes
# (e.g., check duplicates are discarded at the destination)
		publish_topics = []
		publish_topics.append(MQTT_OC2_ALL_RSP_TOPIC)
		if msg.to is not None:
			for dst in msg.to:
				publish_topics.append(MQTT_OC2_DEVICE_RSP_TOPIC+dst)
		# Options and properties are added by the following method
		logger.info("Sending response:\n%s", msg)
		self._send_mqtt_msg(publish_topics, msg, encoder)


	def _recv(self, prop, data):
		""" Retrieve MQTT messages
			
			Internal function to convert MQTT data into otupy `Message` structure and `Encoder`.
			The `encoder` is derived from the HTTP header, to provide the ability to manage multiple
			clients that use different encoding formats.
			:param data: MQTT  message.
			:return: An otupy `Message` (first) and an `Encoder` instance (second).
		"""

		logger.info("Received MQTT payload: \n%s", data)
		msg, encoder = self._frommqtt(prop, data)
  			
		return msg, encoder
	
	def receive(self, callback, encoder):
		""" Listen for incoming messages

			This method implements the :py:class:`~otupy.core.transfer.Transfer` interface 
			to listen for and receive OpenC2 messages.
			Note that only Consumers can use this method (it will fail if a Producer invokes it).

			The internal implementation uses Paho MQTT client. The method invokes the `callback`
			for each received message, which must be provided by a `Consumer` to properly dispatch 
			:py:class:`~otupy.core.command.Command`s to the relevant server(s). 
			It also takes an :py:class:`~otupy.core.encoder.Encoder` that is used to create
			responses to `Command`\s encoded with unknown encoders.

			This implemnetation sends the response to the device-specific topic, if available from
			the command (it SHOULD be available according to the Specification requirements, but
			we want to be be safe and robust about buggy implementations).

			:param callback: The function that is invoked to process OpenC2 messages.
			:param encoder: Default `Encoder` instance to respond to unknown or wrong messages.
			:return: None

		"""
		assert self.role == OpenC2Role.Consumer

		self.message_processing_callback = callback

		try:
			logger.info("Waiting for MQTT messages")
			self.client.loop_forever()
		except KeyboardInterrupt:
			logger.info("Stopping processing MQTT messages")

	def _mqttmsg_to_str(self, msg: mqtt_client.MQTTMessage):
		return "Properties: " + str(msg.properties) + " <-> Payload: " + str(msg.payload)
#
#
#class HTTPSTransfer(HTTPTransfer):
#	""" HTTP Transfer Protocol with SSL
#
#		This class provides an implementation of the Specification. It builds on Flask and so it is not
#		suitable for production environments.
#
#		Use `HTTPSTransfer` to build OpenC2 communication stacks in `Producer` and `Consumer`.
#		Usage and methods of `HTTPSTransfer` are semanthically the same as for `HTTPTransfer`.
#	"""
#	def __init__(self, host, port = 443, endpoint = '/.well-known/openc2'):
#		""" Builds the `HTTPSTransfer` instance
#
#			The `host` and `port` parameters are used either for selecting the remote server (`Producer`) or
#			for local binding (`Consumer`). This implementation only supports TCP as transport protocol.
#			:param host: Hostname or IP address of the OpenC2 server.
#			:param port: Transport port of the OpenC2 server.
#			:param endpoint: The remote endpoint to contact the OpenC2 server (`Producer` only).
#		"""
#		HTTPTransfer.__init__(self, host, port, endpoint, usessl=True)
#		self.ssl_context = "adhoc"
#
#
