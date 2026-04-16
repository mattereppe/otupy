import otupy
import otupy.encoders.json as json
import otupy.profiles.slpf

import logging

import sys
sys.path.insert(0, "../profiles/")

import esm

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


with open('test2.xml','r') as x:
#with open('test.xml','r') as x:
	s=x.read().replace('\n','')

cmd=json.JSONEncoder.decode(s, otupy.Response)

#print("Type: " , type(cmd.target.getObj()))

