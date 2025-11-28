import logging
import sys

import otupy as oc2
from otupy.actuators.Ebpf.Ebpf_actuator import EbpfActuator
from otupy.profiles.ebpf.profile import Profile
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)
logger = logging.getLogger('openc2')
	
def main():

	asset_id = 'test'
	actuators = {}
	actuators[(Profile.nsid,asset_id)]=EbpfActuator()

	c = oc2.Consumer("ebpfConsummer", actuators, JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))


	c.run()




if __name__ == "__main__":

	main()
