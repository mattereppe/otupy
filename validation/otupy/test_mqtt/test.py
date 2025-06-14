import otupy
import otupy.encoders.xml as xml
import otupy.profiles.slpf

import logging

import sys
sys.path.insert(0, "../profiles/")

import esm

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


#with open('test2.xml','r') as x:
with open('test.xml','r') as x:
	s=x.read().replace('\n','')

cmd=xml.XMLEncoder.decode(s, otupy.Response)

#print("Type: " , type(cmd.target.getObj()))

