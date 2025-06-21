#!../.venv/bin/python3
# Example to use the OpenC2 library
#

import logging
import sys
import datetime

import otupy as oc2


from otupy.encoders.json import JSONEncoder
from otupy.encoders.cbor import CBOREncoder
from otupy.transfers.mqtt import MQTTTransfer
from otupy.actuators.iptables_actuator import IptablesActuator
import otupy.profiles.slpf as slpf
import otupy.profiles.dumb as dumb
from otupy.actuators.slpf.dumb_actuator import DumbActuator

#logging.basicConfig(filename='consumer.log',level=logging.DEBUG)
#logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)
#logger = logging.getLogger('openc2:'+__name__)
# Declare the logger name
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.DEBUG)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))
# Add both handlers to the logger
logger.addHandler(stdout_handler)
# Add file logger
file_handler = logging.FileHandler("server.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True, datefmt='%t'))
logger.addHandler(file_handler)
# ?????
hdls = [ stdout_handler , file_handler]
	
def main():

# Instantiate the list of available actuators, using a dictionary which key
# is the assed_id of the actuator.
	actuators = {}
	actuators[(slpf.Profile.nsid,'iptables')]=DumbActuator()
	actuators[('x-dumb','dumb')]=DumbActuator()
	device_id="testconsumer"

	c = oc2.Consumer(device_id, actuators, JSONEncoder(), MQTTTransfer("150.145.8.217", 1883, device_id=device_id, profiles=[slpf.Profile.nsid]))
#	c = oc2.Consumer(device_id, actuators, CBOREncoder(), MQTTTransfer("150.145.8.217", 1883, device_id=device_id, profiles=[slpf.Profile.nsid]))

	c.run()


if __name__ == "__main__":
	main()
