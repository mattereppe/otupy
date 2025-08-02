import logging
import threading
import paho.mqtt.client as mqtt
from werkzeug.exceptions import UnsupportedMediaType

import otupy as oc2
from otupy.transfers.http.message import Message  # Re-using message structure for consistency

logger = logging.getLogger(__name__)
""" The logging facility in otupy """


class MQTTTransfer(oc2.Transfer):
    """ MQTT Transfer Protocol

       This class provides an implementation of the Transfer interface for MQTT.
       It allows OpenC2 Producers and Consumers to communicate via an MQTT broker.
       It is designed for both sending commands and listening for them within the
       same framework.
    """

    def __init__(self, broker_host, broker_port=1883, command_topic='openc2/command', response_topic='openc2/response'):
        """ Builds the MQTTTransfer instance

          :param broker_host: Hostname or IP address of the MQTT broker.
          :param broker_port: Transport port of the MQTT broker.
          :param command_topic: The MQTT topic for publishing commands.
          :param response_topic: The MQTT topic for publishing responses.
       """
        self.broker_host = broker_host
        self.broker_port = int(broker_port)
        self.command_topic = command_topic
        self.response_topic = response_topic

        # Each transfer instance gets its own client
        # A unique client_id avoids session issues if multiple clients connect
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.connect(self.broker_host, self.broker_port, 60)

        # For the send method to receive a response
        self._response_payload = None
        self._response_received = threading.Event()

        logger.info(f"MQTTTransfer initialized for broker {self.broker_host}:{self.broker_port}")

    def _serialize(self, msg: oc2.Message, encoder: oc2.Encoder) -> bytes:
        """ Convert otupy 'Message' to a byte payload for MQTT. """
        if encoder is None:
            encoder = oc2.Encoder()  # Default to JSON encoder

        # The message object is encoded directly. All metadata like version
        # and content_type is part of the serialized object.
        m=Message()
        m.set(msg)
        return encoder.encode(m)

    def _frommqtt(self, mqtt_message, encoder: oc2.Encoder) -> tuple[oc2.Message, oc2.Encoder, str | None]:
        """Convert MQTT message to otupy `Message`.

        """
        if encoder is None:
            encoder = oc2.Encoder()
        payload = mqtt_message.payload
        properties = getattr(mqtt_message, 'properties', None)

        # Estrai le User Properties (solo con MQTT v5)
        user_props = {}
        if properties and hasattr(properties, 'UserProperty'):
            for key, value in properties.UserProperty:
                user_props[key.lower()] = value
            auth_header = user_props.get('authorization')

        try:
            m = payload.decode('utf-8') if isinstance(payload, bytes) else payload
            msg = encoder.decode(m, Message).get()
        except Exception as e:
            logger.error(f"Failed to deserialize MQTT payload: {e}")
            raise oc2.EncoderError(f"Cannot decode payload: {payload}") from e

        try:
            msg.status = msg.content.get('status')
        except Exception:
            msg.status = None

        # Estrai auth_info dal campo Authorization se presente
        auth_info = None

        return msg, auth_info

    def send(self, msg: oc2.Message, encoder: oc2.Encoder, auth_info=None) -> oc2.Message:
        """ Sends an OpenC2 message and waits for a response.

          This method implements the Producer logic. It publishes a command to the
          command topic, subscribes to the response topic, and waits for a
          corresponding response message.

          :param msg: The message to send (otupy `Message`).
          :param encoder: The encoder to use for serializing the `msg`.
          :param auth_info: Not used in this MQTT implementation, but kept for interface compatibility.
          :return: An OpenC2 response message (`Message`) or None if timeout occurs.
       """

        # Define the on_message callback for the 'send' operation
        def on_send_message(client, userdata, mqtt_msg):
            """Callback to handle the incoming response."""
            logger.info(f"Producer received response on topic '{mqtt_msg.topic}'")
            try:
                # We assume this message is the response we are waiting for.
                # A robust implementation would check a correlation ID (e.g., request_id).
                response_msg,auth_info = self._frommqtt(mqtt_msg,encoder)
                logger.info(f"Response received: {response_msg}")

                self._response_payload = response_msg
                self._response_received.set()  # Signal that the response has been received
            except Exception as e:
                logger.error(f"Error processing response in producer: {e}")
                self._response_payload = None
                self._response_received.set()  # Signal to unblock, even on error

        # Clear the event and payload from any previous send
        self._response_received.clear()
        self._response_payload = None

        # Assign the specific callback for this operation
        self.client.on_message = on_send_message

        # Subscribe to the response topic
        self.client.subscribe(self.response_topic)

        # Start the network loop in a background thread
        self.client.loop_start()

        # Serialize and publish the command message
        payload = self._serialize(msg, encoder)
        if auth_info is not None:
            pass
        logger.info(f"Producer publishing to topic '{self.command_topic}':\n{payload}")
        self.client.publish(self.command_topic, payload)

        # Wait for the response to be received, with a timeout
        received = self._response_received.wait(timeout=20.0)  # 10-second timeout

        # Stop the background network loop and unsubscribe
        self.client.loop_stop()
        self.client.unsubscribe(self.response_topic)

        if not received:
            logger.error("Producer timed out waiting for a response.")
            return None
        res=self._response_payload.content
        if res['status'].value == 401:
            logger.error("Unauthorized access - HTTP 401")
            # print(response.text)
            e=self._serialize(self._response_payload,encoder)
            raise PermissionError(f"{e}")

        logger.info(f"Producer returning response: {self._response_payload}")
        return self._response_payload

    def receive(self, callback, encoder):
        """ Listens for incoming messages and processes them.

          This method implements the Consumer logic. It subscribes to the command
          topic and enters a permanent loop. For each message received, it invokes
          the provided callback function and publishes the returned response.

          :param callback: The function to invoke for processing OpenC2 messages.
          :param encoder: Default `Encoder` instance to use for messages.
        """

        # Define the on_message callback for the 'receive' operation
        def on_receive_message(client, userdata, mqtt_msg):
            """Callback to handle incoming commands."""
            logger.info(f"Consumer received command on topic '{mqtt_msg.topic}'")
            try:
                # Deserialize the command from the payload
                command,auth_info = self._frommqtt(mqtt_msg,encoder)
                logger.info(f"Received command: {command}")

                # Process the command using the application's callback function
                # The auth_info parameter is passed as None for MQTT
                response_msg = callback(command, auth_info=None)

                # If the callback provides a response, serialize and publish it
                if response_msg:
                    response_payload = self._serialize(response_msg, encoder)
                    logger.info(
                        f"Consumer publishing response to topic '{self.response_topic}':\n{response_payload}")
                    self.client.publish(self.response_topic, response_payload)
                else:
                    logger.info("No response generated by callback.")

            except Exception as e:
                # If deserialization or callback processing fails, log the error.
                # A production system might publish an OpenC2 error response.
                logger.error(f"Error processing command in consumer: {e}")

        # Assign the callback and subscribe to the command topic
        self.client.on_message = on_receive_message
        self.client.subscribe(self.command_topic)

        # Enter the blocking network loop to listen indefinitely
        logger.info(f"Consumer listening for commands on topic '{self.command_topic}'...")
        self.client.loop_forever()