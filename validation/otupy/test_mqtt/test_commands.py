import pytest
import os
import logging
import ipaddress
import json
import cbor2
import json_schema_validation

from helpers import load_json, load_cbor, load_files, send_raw_message, send_raw_message_cbor
from otupy import Encoder, Command, Response, Message, StatusCode, EncoderError
import otupy.profiles.slpf
import otupy.transfers.mqtt
import otupy.transfers.mqtt.message as mqtt
from otupy.encoders.json import JSONEncoder
from otupy.encoders.cbor import CBOREncoder

import json_schema_validation

import sys
sys.path.insert(0, "../profiles/")

import acme
import mycompany
import mycompany_capX
import mycompany_dots
import mycompany_nox
import mycompany_specialchar
import mycompany_with_underscore
import example
import esm
import digits
import digits_and_chars


# Parameters to get good and bad samples of json messages
command_path_good = "../../openc2-json-schema/tests/commands/good"
command_path_bad = "../../openc2-json-schema/tests/commands/bad"
command_path_good_cbor = "../../openc2-cbor-samples/tests/commands/good"
command_path_bad_cbor = "../../openc2-cbor-samples/tests/commands/bad"


class JSONDump(logging.Filter):
	def filter(self, record):
		return  record.getMessage().startswith("HTTP Request Content") or record.getMessage().startswith("HTTP Response Content") 


def check_command(cmd):
	assert cmd is not None


# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 
# 
# The command in openc2-json-schema/src/test/resources/commands/good/deny_uri_actuator_multiple.json
# does not conform to the language specification, since the actuator is defined as "Choice", hence
# it cannot contain multiple values.
# I removed the x-acme actuator and renamed the file to deny_uri.json; I moved the original file to 
# the "bad" examples. 
#
# The command in openc2-json-schema/src/test/resources/commands/good/allow_ipv6net_wikipedia8_prefix2.json
# uses an IPv6 address as ipv6net. The standard refers to RFC 8200, but that RFC does not state anything
# about IPv6 addresses/networks. The standard also says that if the prefix is omitted, the IPv6-Net
# refers to a single host address. This is perfectly aligned with the general understanding that a
# network address must have all bits zeroed in the host part (and it is also compliant with the python
# ipaddress package. Based on these considerations, I changed the IP address to "2001:db8:a::/64" and
# moved the original file to the "bad" examples.
# The same happened for openc2-json-schema/src/test/resources/commands/good/allow_ipv6net_prefix.json.
# Fixed the same way as the previous file, by setting the address to "3ffe:1900:4545:3:0:0:0:0/64".
# Done again for openc2-json-schema/src/test/resources/commands/good/allow_ipv4net_cidr.json.
# Fixed address to: "127.0.0.0/8"
#
# The command in openc2-json-schema/src/test/resources/commands/good/query_features_ext_target.json
# (and maybe other files) uses a uncommon definition for a sort of extension to features. It
# defines the new x-acme:feature target as a map, containing the standard-style feature target
# definition: "'target': {'x-acme:features': {'features': ['versions', 'profiles', 'schema']}}"
# This does not look aligned with the definition in the Language Specification, but since it is
# an extension I did not change it and provided the implementation according to this definition.
# 
# >>>>>>>>>>>>>> Keep in mind to redo this if you update the repository. <<<<<<<<<<<<<<<<<<<<<<<<
#
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 


#def test_load_and_decoding():
#	# There should be no dirs in the folder I'm looking for commands, but I filter out directories just to be sure
#	cmds_files = [
#    os.path.join(command_path_good,f) for f in os.listdir(command_path_good) if os.path.isfile(os.path.join(command_path_good, f))
#	]
#	print(cmds_files)
#
##cmds_files = [ "openc2-json-schema/src/test/resources/commands/good/start_container_ext_target_ext_actuator_ext_args.json" ]
#
#	for f in cmds_files:
#		print("file ", f)
#		create_command(file=f)

def validate_json(caplog):
	""" Check the openc2 json messages exchanged between the consumer and the producer are valid according to the schema """
	
@pytest.mark.parametrize("cmd", load_json(command_path_good) )
def test_sending(cmd, create_producer_mqtt, caplog):
	""" Test 'good' messages are successfully sent to the remote party and a response is received.

		Validate the openc2 json messages exchanged. The response is often an error because the majority
		of features are not implemented in the available actuators.
	"""
	c = Encoder.decode(Command, cmd)

# Filter the log to get what I need
	logger = logging.getLogger("otupy.transfers.mqtt.mqtt_transfer")
	logger.addFilter(JSONDump())

	check_command(c)
	print("Command: ", c)
	with caplog.at_level(logging.INFO):
		resp = create_producer_mqtt.sendcmd(c,consumers=["testconsumer"])

	assert type(resp) == list
#	if len(resp) > 1:
	assert type(resp[0]) == Message
	assert type((resp[0]).content) == Response

	validate_json(caplog)
	assert resp[0].content['status'] == StatusCode.BADREQUEST or \
		resp[0].content['status'] == StatusCode.NOTIMPLEMENTED or \
		resp[0].content['status'] == StatusCode.NOTFOUND
		

@pytest.mark.parametrize("cmd", load_cbor(command_path_good_cbor) )
def test_sending_cbor(cmd, create_producer_mqtt, caplog):
	""" Test 'good' messages are successfully sent to the remote party and a response is received.

		Validate the openc2 json messages exchanged. The response is often an error because the majority
		of features are not implemented in the available actuators.
	"""
	c = Encoder.decode(Command, cmd)

	check_command(c)
	print("Command: ", c)
	with caplog.at_level(logging.INFO):
		resp = create_producer_mqtt.sendcmd(c,consumers=["testconsumer"])

	assert type(resp) == list
#	if len(resp) > 1:
	assert type(resp[0]) == Message
	assert type((resp[0]).content) == Response

	validate_json(caplog)
	assert resp[0].content['status'] == StatusCode.BADREQUEST or \
		resp[0].content['status'] == StatusCode.NOTIMPLEMENTED or \
		resp[0].content['status'] == StatusCode.NOTFOUND
		


@pytest.mark.parametrize("file",  load_files(command_path_bad)  )
def test_response_to_invalid_commands(file, mqtt_body):
	""" Send invalid commands and check a BADREQUEST is returned

		Read invalid commands from file and send them to a Consumer. Commands are not encoded (because invalid).
		Check that a BADREQUEST status is returned.
	"""
	print("Command json: ", file)
	# It may also raises while loading the files, since they may be empty
	count = 0
#	for f in cmd_files:
#print("File: " , file)
	with open(file, 'r') as fcmd:
		try:
			cmd = json.load(fcmd) 
		except:
			# In the bad exampes, 1 file is empty. If more than one file cannot be read, something has changed!
			if fcmd.read() == '':
				cmd = {}	
			else:
				raise ValueError("Unable to read json")
#		print("Command json: ", cmd)
		mqtt_body['body']['openc2']['request'] = cmd
#		print("HTTP body: ", json.dumps(http_body))
		response = send_raw_message(json.dumps(mqtt_body))

		msg = JSONEncoder.decode(response, mqtt.Message)
		assert msg.body.getObj().getObj()['status'] == StatusCode.BADREQUEST
		
@pytest.mark.parametrize("file",  load_files(command_path_bad_cbor)  )
def test_response_to_invalid_commands_cbor(file, mqtt_body):
	""" Send invalid commands and check a BADREQUEST is returned

		Read invalid commands from file and send them to a Consumer. Commands are not encoded (because invalid).
		Check that a BADREQUEST status is returned.
	"""
	print("Command cbor: ", file)
	# It may also raises while loading the files, since they may be empty
	count = 0
#	for f in cmd_files:
#print("File: " , file)
	with open(file, 'rb') as fcmd:
		try:
			cmd = cbor2.load(fcmd) 
		except:
			# In the bad exampes, 1 file is empty. If more than one file cannot be read, something has changed!
			cmd = {}	
#		print("Command json: ", cmd)
		mqtt_body['body']['openc2']['request'] = cmd
#		print("HTTP body: ", json.dumps(http_body))
		response = send_raw_message_cbor(cbor2.dumps(mqtt_body))
		print("CBOR response: ", response)

		msg = CBOREncoder.decode(response, mqtt.Message)
		assert msg.body.getObj().getObj()['status'] == StatusCode.BADREQUEST
		

