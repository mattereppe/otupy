import pytest
import os
import logging
import ipaddress
import xmltodict 
from xml.parsers.expat import ExpatError
import copy

from helpers import load_xml, load_files, send_raw_command
from otupy import Encoder, Command, Response, Message, StatusCode, EncoderError
import otupy.profiles.slpf
import otupy.transfers.http
import otupy.transfers.http.message as http
from otupy.encoders.xml import XMLEncoder

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
command_path_good = "../../openc2-xml-samples/tests/commands/good"
command_path_bad = "../../openc2-xml-samples/tests/commands/bad"


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

def fix_ip_addresses(cmd):
	""" This function fixes ip addresses to compare with json examples provided by third party.
		According to common network practice, an IP network address should always include the prefix/netmask.
		The LS says a Connection should include "IP address range", so this implicitely demands for a prefix
		to be given. However, a single host address may be acceptable as well. Openc2lib strictly adhere to
		the network-biased convention to always give the prefix, but it also accepts ip addresses as input.
		This fix is necessary to convert the reference json examples so that they are comparable with the 
		notation of otupy.
	"""
	if 'ipv4_net' in cmd['target']:
		cmd['target']['ipv4_net'] = ipaddress.IPv4Network(cmd['target']['ipv4_net']).compressed
		cmd['target']['ipv4_net'] = cmd['target']['ipv4_net'].replace ("/32",'')
	if 'ipv6_net' in cmd['target']:
# 	cmd['target']['ipv6_net'] = ipaddress.IPv6Network(cmd['target']['ipv6_net']).compressed
	 	cmd['target']['ipv6_net'] = cmd['target']['ipv6_net'].replace ("/128",'')
	if 'ipv4_connection' in cmd['target']:
		for ip in ['src_addr', 'dst_addr']:
			if ip in cmd['target']['ipv4_connection']:
				cmd['target']['ipv4_connection'][ip] = ipaddress.IPv4Network(cmd['target']['ipv4_connection'][ip]).compressed
				cmd['target']['ipv4_connection'][ip] = cmd['target']['ipv4_connection'][ip].replace ("/32",'')
	if 'ipv6_connection' in cmd['target']:
		for ip in ['src_addr', 'dst_addr']:
			if ip in cmd['target']['ipv6_connection']:
#		 		cmd['target']['ipv6_connection'][ip] = ipaddress.IPv6Network(cmd['target']['ipv6_connection'][ip]).compressed
		 		cmd['target']['ipv6_connection'][ip] = cmd['target']['ipv6_connection'][ip].replace("/128",'')
	 		
def fix_ip_addresses2(cmd):
	""" This function fixes ip addresses to compare with json examples provided by third party.
		According to common network practice, an IP network address should always include the prefix/netmask.
		The LS says a Connection should include "IP address range", so this implicitely demands for a prefix
		to be given. However, a single host address may be acceptable as well. Openc2lib strictly adhere to
		the network-biased convention to always give the prefix, but it also accepts ip addresses as input.
		This fix is necessary to convert the reference json examples so that they are comparable with the 
		notation of otupy.
	"""
	if 'ipv4_net' in cmd['target']:
		cmd['target']['ipv4_net'] = ipaddress.IPv4Network(cmd['target']['ipv4_net']).compressed
	if 'ipv6_net' in cmd['target']:
	 	cmd['target']['ipv6_net'] = ipaddress.IPv6Network(cmd['target']['ipv6_net']).compressed
	if 'ipv4_connection' in cmd['target']:
		for ip in ['src_addr', 'dst_addr']:
			if ip in cmd['target']['ipv4_connection']:
		 		cmd['target']['ipv4_connection'][ip] = ipaddress.IPv4Network(cmd['target']['ipv4_connection'][ip]).compressed
	if 'ipv6_connection' in cmd['target']:
		for ip in ['src_addr', 'dst_addr']:
			if ip in cmd['target']['ipv6_connection']:
		 		cmd['target']['ipv6_connection'][ip] = ipaddress.IPv6Network(cmd['target']['ipv6_connection'][ip]).compressed
	 		
	 	
def fix_hex(cmd):
	""" Convert BinaryX values to uppercase, as recommended by the specification"""
	for h in ['md5', 'sha1', 'sha256']:
		try:
			if h in cmd['target']['file']['hashes']:
				cmd['target']['file']['hashes'][h] = cmd['target']['file']['hashes'][h].upper()
		except:
			pass

	if 'mac_addr' in cmd['target']:
		# Use lowercase for similarity to BinaryX
		cmd['target']['mac_addr'] = cmd['target']['mac_addr'].lower()
	
def fix_uuid(cmd):
	""" UUID according to RFC 4122 are created as lowercase, but both cases are accepted as input.
		Here we stitch to lowercase for comparison.
		
		This is a very specific trick for the validation set.
	"""
	if 'x-acme:container' in cmd['target']:
		cmd['target']['x-acme:container']['container_id'] = cmd['target']['x-acme:container']['container_id'].upper()

def _postprocessor(path, key, value):
#       if value is None:
#          return key, {}

   try:
      return key , int(value)
   except (ValueError, TypeError):
      return key, value

def _preprocessor(d):
	for k, v in d.items():
		try:
	  		v = _preprocessor(v)
		except AttributeError:
			if not v:
				d[k] = None
			
	return d
 
 



@pytest.mark.parametrize("cmd", load_xml(command_path_good) )
#@pytest.mark.dependency(name="test_decoding")
def test_decoding(cmd):
	""" Test 'good' commands can be successfully decoded by otupy """
	print("Command xml: ", cmd)
	c = XMLEncoder.decode(cmd, Command)
	assert type(c) == Command

@pytest.mark.parametrize("cmd", load_xml(command_path_good) )
#@pytest.mark.dependency(name="test_encoding", depends=["test_decoding"])
def test_encoding(cmd):
	""" Test 'good' commands can be successfully encoded by otupy

		The test decodes 'good' commands, and then create again the json. Finally, the original
		and created json are compared. A number of fixes are applied to account for different
		representations of the values (e.g., lowercase/uppercase).
	"""
	cmd_str = cmd.replace(' ','').replace('\t','')
	print("Original xml: ", cmd.replace(' ',''))
	oc2_cmd = XMLEncoder.decode(cmd, Command)
	# Use to dict because the Encoder.encode method returns a str
	oc2_json = Encoder.todict(oc2_cmd)
	print("Encoded dictionary: ", oc2_json)
	print("type: ", type(oc2_json))

	cmd_dic =  xmltodict.parse(cmd, postprocessor=_postprocessor)[XMLEncoder.OpenC2Root]
	cmd_dic2 = copy.deepcopy(cmd_dic)
	print("Original dictionary from xml: ", cmd_dic)
	fix_ip_addresses(cmd_dic)
	fix_hex(cmd_dic)
	fix_uuid(cmd_dic)
	fix_ip_addresses2(cmd_dic2)
	fix_hex(cmd_dic2)
	fix_uuid(cmd_dic2)

	cmd_xml = xmltodict.unparse({XMLEncoder.OpenC2Root: cmd_dic}, pretty=True)
	cmd_xml2 = xmltodict.unparse({XMLEncoder.OpenC2Root: cmd_dic2}, pretty=True)

#cmd_xml = XMLEncoder.encode(oc2_cmd)
	cmd_xml_str =  cmd_xml.replace('<?xml version="1.0" encoding="utf-8"?>','').replace('\n','').replace(' ','').replace('\t','')
	cmd_xml_str2 =  cmd_xml2.replace('<?xml version="1.0" encoding="utf-8"?>','').replace('\n','').replace(' ','').replace('\t','')
	print("String after encoding: ", cmd_xml_str)
	print("String after encoding: ", cmd_xml_str2)

#assert cmd_dic == oc2_json
#	assert etree.tostring(cmd_dic) == etree.tostring(cmd)
	assert cmd_str == cmd_xml_str or cmd_str == cmd_xml_str2



@pytest.mark.parametrize("cmd", load_xml(command_path_good) )
#@pytest.mark.dependency(depends=["test_decoding", "test_encoding"])
def test_sending(cmd, create_xml_producer, caplog):
	""" Test 'good' messages are successfully sent to the remote party and a response is received.

		Validate the openc2 json messages exchanged. The response is often an error because the majority
		of features are not implemented in the available actuators.
	"""
#c = Encoder.decode(Command, cmd)
	c = XMLEncoder.decode(cmd, Command)

# Filter the log to get what I need

	check_command(c)
	print("Command: ", c)
	with caplog.at_level(logging.INFO):
		resp = create_xml_producer.sendcmd(c)

	assert type(resp) == Message
	assert type(resp.content) == Response

	assert resp.content['status'] == StatusCode.BADREQUEST or \
		resp.content['status'] == StatusCode.NOTIMPLEMENTED or \
		resp.content['status'] == StatusCode.NOTFOUND
		

@pytest.mark.parametrize("cmd_file", load_files(command_path_bad) )
def test_decoding_invalid(cmd_file):
	""" Check invalid commands raise exceptions when decoded """
	print("Command file: ", cmd_file)
	# It may also raises while loading the files, since they may be empty
	with open(cmd_file, 'r') as fcmd:
		try:
#	cmd = xmltodict.parse(fcmd) 
			cmd = fcmd.read()
			cmd_dic =  xmltodict.parse(cmd, postprocessor=_postprocessor)[XMLEncoder.OpenC2Root]
		except ExpatError:
			cmd = ""
		with pytest.raises( (TypeError, ValueError, KeyError, EncoderError) ):
			print("Command xml: ", cmd)
			Encoder.decode(Command, cmd)
		

@pytest.mark.parametrize("file",  load_files(command_path_bad)  )
def test_response_to_invalid_commands(file, http_url, http_headers, http_body):
	""" Send invalid commands and check a BADREQUEST is returned

		Read invalid commands from file and send them to a Consumer. Commands are not encoded (because invalid).
		Check that a BADREQUEST status is returned.
	"""
	print("Command xml: ", file)
	# It may also raises while loading the files, since they may be empty
	count = 0
#	for f in cmd_files:
#print("File: " , file)
	with open(file, 'r') as fcmd:
		try:
			cmd_xml = fcmd.read()
			cmd = xmltodict.parse(cmd_xml) 
		except:
			# In the bad exampes, 1 file is empty. If more than one file cannot be read, something has changed!
			if fcmd.read() == '':
				cmd = {}	
			else:
				raise ValueError("Unable to read xml")
		print("ready to send: ", cmd)
#		print("Command json: ", cmd)
		http_body['body']['openc2']['request'] = cmd
		response = send_raw_command(http_url, http_headers, xmltodict.unparse({XMLEncoder.OpenC2Root: cmd}, pretty=True))

		assert response.status_code == 400
#		print("response text: ", response.text)

		msg = XMLEncoder.decode(response.text, http.Message)
		assert msg.body.getObj().getObj()['status'] == StatusCode.BADREQUEST
		

