#!../.venv/bin/python3
# Example to test the OpenC2 library locally (e.g., with no real Managed Devices)
#

import logging
import sys
import datetime

import otupy as oc2


from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.actuators.slpf.mockup_slpf_actuator import MockupSlpfActuator
import otupy.profiles.slpf as slpf
import otupy.profiles.dumb as dumb
from otupy.actuators.slpf.dumb_actuator import DumbActuator

sys.path.insert(0, "../validation/otupy/profiles/")
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


#logging.basicConfig(filename='consumer.log',level=logging.DEBUG)
#logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)
#logger = logging.getLogger('openc2:'+__name__)
# Declare the logger name
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
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
	actuators[(slpf.Profile.nsid,'iptables')]=MockupSlpfActuator()
	actuators[('x-dumb','dumb')]=DumbActuator()

	c = oc2.Consumer("testconsumer", actuators, JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))

	c.run()


if __name__ == "__main__":
	main()
