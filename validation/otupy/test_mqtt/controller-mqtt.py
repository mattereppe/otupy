#!../.venv/bin/python3
# Example to use the OpenC2 library
#

import logging
import sys

import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.encoders.cbor import CBOREncoder
from otupy.transfers.mqtt import MQTTTransfer, OpenC2Role

import otupy.profiles.slpf as slpf
import otupy.profiles.dumb as dumb



#logging.basicConfig(filename='openc2.log',level=logging.DEBUG)
#logging.basicConfig(stream=sys.stdout,level=logging.INFO)
#logger = logging.getLogger('openc2producer')
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.DEBUG)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))

hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)
# Add file logger
file_handler = logging.FileHandler("controller.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True, datefmt='%t'))
logger.addHandler(file_handler)

def main():
	logger.info("Creating Producer")

	with open('test.json','r') as x:
		s=x.read().replace('\n','')
	
	cmd=JSONEncoder.decode(s, oc2.Command)

	p = oc2.Producer("myproducer", JSONEncoder(), MQTTTransfer("150.145.8.217", 1883, OpenC2Role.Producer, device_id="myproducer"))
#p = oc2.Producer("myproducer", CBOREncoder(), MQTTTransfer("150.145.8.217", 1883, OpenC2Role.Producer, device_id="myproducer"))

#pf = slpf.Specifiers({'hostname':'firewall1', 'named_group':'firewalls', 'asset_id':'iptables'})
#	pf = dumb.dumb({'hostname':'mockup', 'named_group':'testing', 'asset_id':'dumb'})


#	arg = oc2.Args({'response_requested': oc2.ResponseType.complete})
#	arg = slpf.Args({'response_requested': oc2.ResponseType.none})
#	arg = slpf.Args({'response_requested': oc2.ResponseType.complete, 'direction': slpf.Direction.ingress})

#	cmd = oc2.Command(oc2.Actions.query, oc2.Features([oc2.Feature.versions, oc2.Feature.profiles, oc2.Feature.pairs]), arg, actuator=pf)
#	cmd = oc2.Command(oc2.Actions.allow, oc2.IPv4Net("172.19.0.0/24"), arg, actuator=pf)
#	cmd = oc2.Command(oc2.Actions.delete, slpf.RuleID(1), arg, actuator=pf)
#cmd = oc2.Command(oc2.Actions.allow, slpf.RuleID(24), arg, actuator=pf)
#	cmd = oc2.Command(oc2.Actions.query, oc2.Features([oc2.Feature.rate_limit]), arg, actuator=pf)

	logger.info("Sending command: %s", cmd)
# For MQTT, use the same consumer name as device_id used by the Consumer!!!
#	resp = p.sendcmd(cmd, consumers=["testconsumer","myconsumer"])
	resp = p.sendcmd(cmd, consumers=["testconsumer","testconsumer2"])
#	resp = p.sendcmd(cmd, consumers=["testconsumer"])
#	resp = p.sendcmd(cmd)
	for r in resp:
		logger.info("Got response: %s", r)


if __name__ == '__main__':
	main()
