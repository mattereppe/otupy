import pytest
import os
import ipaddress
import xml
import xmltodict
from xml.parsers.expat import ExpatError

from helpers import load_xml, load_files
from otupy import Encoder, Response, StatusCode, EncoderError
import otupy.profiles.slpf
import otupy.transfers.http
import otupy.transfers.http.message as http
from otupy.encoders.xml import XMLEncoder

import sys
sys.path.insert(0, "../profiles/")

import acme
import mycompany
import mycompany_with_underscore
import example
import esm
import digits
import digits_and_chars


# Parameters to get good and bad samples of xml messages
response_path_good = "../../openc2-xml-samples/tests/responses/good"
response_path_bad = "../../openc2-xml-samples/tests/responses/bad"

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 
# 
# The response in good/query_features_all.json does not conform to the definition 3.4.2.17 Version
# that says the Version is Major.Minor version number. This file uses: "1.0-draft-2019-02". 
# I removed the trailing "-draft-2019-02" e put the original file in the bad examples.


@pytest.mark.parametrize("rsp", load_xml(response_path_good) )
@pytest.mark.dependency(name="test_decoding")
def test_decoding(rsp):
	print("Response xml: ", rsp)
	c = XMLEncoder.decode(rsp, Response)
	assert type(c) == Response

@pytest.mark.parametrize("rsp", load_xml(response_path_good) )
#@pytest.mark.dependency(name="test_encoding", depends=["test_decoding"])
def test_encoding(rsp):
	rsp_str = rsp.replace(' ','').replace('\t','')
	print("Original xml: ", rsp_str)
	oc2_rsp = XMLEncoder.decode(rsp, Response)

	rsp_xml = XMLEncoder.encode(oc2_rsp)
	rsp_xml_str =  rsp_xml.replace('<?xml version="1.0" encoding="utf-8"?>','').replace('\n','').replace(' ','').replace('\t','')
	print("String after encoding: ", rsp_xml_str)

#assert cmd_dic == oc2_json
	assert rsp_str == rsp_xml_str 

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

@pytest.mark.parametrize("rsp_file", load_files(response_path_bad) )
def test_decoding_invalid(rsp_file):
	""" Check invalid commands raise exceptions when decoded """
	print("Response file: ", rsp_file)
	# It may also raises while loading the files, since they may be empty
	with open(rsp_file, 'r') as frsp:
		# There is one empty file that raises this exception
		try:
			rsp_str = frsp.read()
			rsp =  xmltodict.parse(rsp_str, postprocessor=_postprocessor)[XMLEncoder.OpenC2Root]
		except ExpatError:
			rsp = ""

		print("Response xml: ", rsp)
		with pytest.raises( (ValueError, KeyError, EncoderError) ):
			Encoder.decode(Response, rsp)
		

