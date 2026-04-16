import pytest
import json
import cbor2
import sys
import requests
from paho.mqtt import client as mqtt_client
import time

from otupy import Encoder, Command

import os
sys.path.insert(0, "../profiles/")

import acme
import mycompany
import mycompany_with_underscore
import example
import esm
import digits
import digits_and_chars
import otupy.profiles.slpf


#def create_command(string = None, file= None):
#	""" Create an otupy command from a json string or file. 
#		
#		It expects the command in a string; alternatively, the file containing the json can be given by
#		specifying its keyword. If both are given, the string is used. """
#	print(file)
#	if string:
#		cmd_dict = json.loads(string)
#	elif file:
#		with open(file, 'r') as f:
#			cmd_dict = json.load(f)
#	else:
#		raise TypeError("Json string or file must be given!")
#
#	print(cmd_dict)
#	return  Encoder.decode(Command, cmd_dict)

def load_files(cmd_path):
	""" Load all files with json commads """
	# There should be no dirs in the folder I'm looking for commands, but I filter out directories just to be sure
	cmds_files = [
    os.path.join(cmd_path,f) for f in os.listdir(cmd_path) if os.path.isfile(os.path.join(cmd_path, f))
	]

# use this if you want to debug a single file
#	cmds_files = [ "openc2-json-schema/src/test/resources/commands/bad/action_notarget.json" ]

	return cmds_files

def load_json(path):
	""" Load an otupy command/response from a json string or file. 
		
		It expects the command in a string; alternatively, the file containing the json can be given by
		specifying its keyword. If both are given, the string is used. """

	files = load_files(path)
# use this if you want to debug a single file
#cmds_files = [ "openc2-json-schema/src/test/resources/commands/bad/action_notarget.json" ]

	lst = []
	for f in files:
		print("Processing file ", f)

		with open(f, 'r') as j:
			lst.append(  json.load(j) )

	return lst

def load_cbor(path):
	""" Load an otupy command/response from a cbor string or file. 
		
		It expects the command in a string; alternatively, the file containing the cbor can be given by
		specifying its keyword. If both are given, the string is used. """

	files = load_files(path)
# use this if you want to debug a single file
#cmds_files = [ "openc2-json-schema/src/test/resources/commands/bad/action_notarget.json" ]

	lst = []
	for f in files:
		print("Processing file ", f)

		with open(f, 'rb') as y:
			b = y.read()
			lst.append(  cbor2.loads(b) )

	return lst

def send_raw_command(url, oc2hdrs, oc2data):
	""" This function emulates a faulty producer that sends invalid openc2 messages (only the body in http) """
	print("Message body: ", oc2data)
	return requests.post(url, data=oc2data, headers=oc2hdrs, verify=False)

def send_raw_message(oc2data):
	""" This function emulates a faulty producer that sends invalid openc2 messages (only the body in mqtt) """

	def on_message(client, userdata, msg):
		print("On message!")
		print("Userdata: ", userdata)
		userdata.append(msg)
		print(userdata)


	userdata = list()
	# Set Connecting Client ID
	client = mqtt_client.Client(client_id="myproducer",
												callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2, 
												protocol=mqtt_client.MQTTv5,
												userdata=userdata)
	client.on_message=on_message

	# OpenC2 does not use Will message (Sec. 2.8)
	client.will_clear()
	# Connect properties 
	connect_properties = mqtt_client.Properties(mqtt_client.PacketTypes.CONNECT)
	connect_properties.SessionExpiryInterval = 20

	ret = client.connect("150.145.8.217", 1883, clean_start=False,
					properties=connect_properties)

	# Set properties according to the Specification
	publish_properties = mqtt_client.Properties(mqtt_client.PacketTypes.PUBLISH)
	if (type(oc2data) == str):
		publish_properties.PayloadFormatIndicator = 0x01 # UTF-8 encoded character data
	else:
		publish_properties.PayloadFormatIndicator = 0x00 # unspecified byte stream
	publish_properties.MessageExpiryInterval = 20
	publish_properties.ContentType = "application/openc2"
	publish_properties.UserProperty = ("msgType", "req")
	publish_properties.UserProperty = ("encoding", "json")

	
	options = mqtt_client.SubscribeOptions(qos=2,
														noLocal=True,
														retainAsPublished=True,
														retainHandling=mqtt_client.SubscribeOptions.RETAIN_SEND_ON_SUBSCRIBE)
	err, mid = client.subscribe("oc2/rsp")
	err, mid = client.subscribe("oc2/rsp/device/myproducer")

	res = client.publish("oc2/cmd/all", oc2data, qos=1,
												retain=True, properties=publish_properties)

	msg=None
	print("test")
	client.loop_start()
	received = False
	while not received:
		print("Sleeping...")
		time.sleep(1)	
		print("userdata: ", userdata)
		if len(userdata) > 0:
			print(userdata[0].payload.decode('utf-8'))
			received = True
	client.loop_stop()

	return userdata[0].payload.decode('utf-8')

def send_raw_message_cbor(oc2data):
	""" This function emulates a faulty producer that sends invalid openc2 messages (only the body in mqtt) """

	def on_message(client, userdata, msg):
		print("On message!")
		print("Userdata: ", userdata)
		userdata.append(msg)
		print(userdata)


	userdata = list()
	# Set Connecting Client ID
	client = mqtt_client.Client(client_id="myproducer",
												callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2, 
												protocol=mqtt_client.MQTTv5,
												userdata=userdata)
	client.on_message=on_message

	# OpenC2 does not use Will message (Sec. 2.8)
	client.will_clear()
	# Connect properties 
	connect_properties = mqtt_client.Properties(mqtt_client.PacketTypes.CONNECT)
	connect_properties.SessionExpiryInterval = 20

	ret = client.connect("150.145.8.217", 1883, clean_start=False,
					properties=connect_properties)

	# Set properties according to the Specification
	publish_properties = mqtt_client.Properties(mqtt_client.PacketTypes.PUBLISH)
	if (type(oc2data) == str):
		publish_properties.PayloadFormatIndicator = 0x01 # UTF-8 encoded character data
	else:
		publish_properties.PayloadFormatIndicator = 0x00 # unspecified byte stream
	publish_properties.MessageExpiryInterval = 20
	publish_properties.ContentType = "application/openc2"
	publish_properties.UserProperty = ("msgType", "req")
	publish_properties.UserProperty = ("encoding", "cbor")

	
	options = mqtt_client.SubscribeOptions(qos=2,
														noLocal=True,
														retainAsPublished=True,
														retainHandling=mqtt_client.SubscribeOptions.RETAIN_SEND_ON_SUBSCRIBE)
	err, mid = client.subscribe("oc2/rsp")
	err, mid = client.subscribe("oc2/rsp/device/myproducer")

	res = client.publish("oc2/cmd/all", oc2data, qos=1,
												retain=True, properties=publish_properties)

	msg=None
	print("test")
	client.loop_start()
	received = False
	while not received:
		print("Sleeping...")
		time.sleep(1)	
		print("userdata: ", userdata)
		if len(userdata) > 0:
			print(userdata[0].payload)
			received = True
	client.loop_stop()

	return userdata[0].payload
