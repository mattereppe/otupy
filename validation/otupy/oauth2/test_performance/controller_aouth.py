#!../../../.oc2-env/bin/python3
# Example to use the OpenC2 library
#

import logging
import sys
import os
import otupy as oc2
import json
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.oauth2.OAuth2Authenticator import OAuth2Authenticator
import otupy.profiles.slpf as slpf



logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Add file logger
file_handler = logging.FileHandler("controller-auth.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True, datefmt='%t'))
logger.addHandler(file_handler)

command_path = "/Users/nicolapoidomani/Desktop/otupy/validation/otupy/oauth2/openc2-commands"
NUM_TESTS = 100



def load_json(path):
    cmds_files = [
        os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]
    lst = []
    for f in cmds_files:
        with open(f, 'r') as j:
            lst.append(json.load(j))
    return lst

def main():
    logger.info("Creating Producer")
    oauth2_config = {  # keycloak config
        'client_id': 'Producer',
        'client_secret': 'RYuumxqGJwXTZP52Of5ImUcWEA4TnTUa',
        'redirect_uri': 'http://127.0.0.1:8000/callback',
        'callback_port': 8000
    }
    actuator_profile = slpf.Specifiers({
        'hostname': 'firewall',
        'named_group': 'firewalls',
        'asset_id': 'iptables'
    })
    args = slpf.Args({'response_requested': oc2.ResponseType.complete})
    oauth2authenticator = OAuth2Authenticator(**oauth2_config)

    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 9000), authenticator=oauth2authenticator)

    cmd_list = load_json(command_path)
    for i in range(1, NUM_TESTS + 1):
        print("Running test #", i)
        for c in cmd_list:
            cmd = oc2.Encoder.decode(oc2.Command, c)
            command = oc2.Command(cmd.action, cmd.target, args, actuator=actuator_profile)

            logger.info("Sending command: %s", command)
            resp = p.sendcmd(command)
            logger.info("Got response: %s", resp)


if __name__ == '__main__':
    main()
