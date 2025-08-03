#!/usr/bin/env python3

import logging
import sys

from otupy.core.producer import Producer
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.transfers.mqtt import MQTTTransfer
import otupy as oc2
import otupy.profiles.slpf as slpf

from otupy.oauth2.OAuth2Authenticator import OAuth2Authenticator

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('openc2producer')


def main():
    """Create an OAuth2 Producer and send commands"""

    # OAuth2 configuration
    oauth2_config = {
        'client_id': 'jWcEjOQG0I0MdcxsRdGFS5Ca',
        'client_secret': 'l9KX9UhQNEDyzBxWYe3Ot6OxcvN7Cask6aBdFkEL0UM2gsSQ',
        'redirect_uri': 'http://127.0.0.1:8000/callback',
        'callback_port': 8000
    }
    oauth2authenticator = OAuth2Authenticator(**oauth2_config)

    try:
        transfer = MQTTTransfer(
            broker_host="test.mosquitto.org",
            broker_port=1883)

        producer = Producer(
            producer="producer.example.net",
            encoder=JSONEncoder(),
            transfer=HTTPTransfer("127.0.0.1", 8080),
            authenticator=oauth2authenticator
        )
        prod = Producer(
            producer="producer.example.net",
            encoder=JSONEncoder(),
            transfer=transfer,
            authenticator=oauth2authenticator
        )
        actuator_profile = slpf.Specifiers({
            'hostname': 'firewall',
            'named_group': 'firewalls',
            'asset_id': 'iptables'
        })

        args = slpf.Args({'response_requested': oc2.ResponseType.complete})

        # Example command: query features
        cmd = oc2.Command(
            oc2.Actions.query,
            oc2.Features([oc2.Feature.versions, oc2.Feature.profiles, oc2.Feature.pairs]),
            args,
            actuator=actuator_profile
        )
        cmd2 = oc2.Command(oc2.Actions.update,
                          oc2.File({'path': 'http://192.168.197.128:8080', 'name': 'iptables-rules.v4'}), args,
                          actuator=actuator_profile)

        cmd3 = oc2.Command(oc2.Actions.allow, oc2.IPv4Net('130.0.16.0'), args, actuator=actuator_profile)

        response = prod.sendcmd(cmd)
        # prod.sendcmd(cmd3) #sencond time with saved token

    except ValueError as ve:
        logger.error("Configuration error: %s", ve)
        sys.exit(1)
    except TimeoutError as te:
        logger.error("Authentication timeout: %s", te)
        sys.exit(1)
    except Exception as e:
        logger.error("Error while sending command: %s", e)
        import traceback
        logger.error("Full traceback: %s", traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting OpenC2 Producer with OAuth2...")
    logger.info("Sending Command...")

    try:
        main()
        logger.info("OpenC2 Producer completed successfully")
    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
        sys.exit(0)
    except Exception as ex:
        logger.error(f"Unhandled exception: {ex}")
        import traceback

        logger.error("Full traceback: %s", traceback.format_exc())
        sys.exit(1)