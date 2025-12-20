""" MIRANDA Connector 

	To run the connector, either download the source code or install from ``PyPI`` (see 
	`setup <https://otupy.readthedocs.io/en/latest/download.html#download-and-setup>`__).

	Run the connector: ::
		
		python3 connector.py [-c | --config  <config.yaml>]

"""

		

import logging
from argparse import ArgumentParser
from glob import glob
from os.path import dirname

from yaml import safe_load

# noinspection PyUnusedImports
import otupy.actuators  # Do not remove! It is necessary to find the registered actuators.
# noinspection PyUnusedImports
import otupy.encoders  # Do not remove! It is necessary to find the registered encoders.
# noinspection PyUnusedImports
import otupy.transfers  # Do not remove! It is necessary to find the registered transferers.
from otupy import Actuators, Encoders, Transfers
from otupy import Consumer, LogFormatter

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(LogFormatter(datetime=True,name=True))
hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)



def main() -> None:
    """
    The main function.

    :raise RuntimeError: if something goes wrong
    """

    # Parse the CLI arguments.
    arguments = ArgumentParser()
    arguments.add_argument("-c", "--config", default=f"{dirname(__file__)}/connector.yaml",
                           help="path to the configuration file")
    args = arguments.parse_args()

    # Parse the configuration file.
    with open(args.config) as config_file:
        config = safe_load(config_file)

        try:  
            consumer = config["consumer"]	
            configs = config["configs"]
            connector = config["id"]
        except:
            logger.error("Missing configuration item: %s", e)
            exit

        actuators = {}
        for file in glob(f"{configs}/**/*.yaml", recursive=True):
            with open(file) as f:
                data = safe_load(f)
                for name, values in data.items():
                    # The name of the configuration section is currently not used. 
                    # It may be used in future releases when a better mechanism to
					# dispatch commands to actuators is implemented in the consumer
					# (for now, the consumer dispatches to 1 actuator only, based on
					# its profile and actuator_id).
                    logger.info("Loading actuator: %s", name)
                    identifier = values["actuator"]
                    if identifier not in Actuators:
                        raise RuntimeError(f"{identifier} is not a registered actuator")

                    # By default, we give the actuator this consumer, if the configuration file
				    # does not provide one
                    if 'consumer' not in values:
                       values['consumer'] = consumer
                    clazz = Actuators[identifier]
                    parameters = dict(values)
                    del parameters["actuator"]
                    del parameters["profile"]

                    profile = values["profile"]
                    actuators[(profile, values["specifiers"]["asset_id"])] = clazz(**parameters)

        # Load the encoder.
        if consumer['encoding'] not in Encoders.__members__:
            raise RuntimeError(f"{consumer['encoding']} is not a registered encoding schema")
        encoder = Encoders[consumer['encoding']]

        # Load the transferer (beautiful name, eh?).
        if consumer['transfer'] not in Transfers:
            raise RuntimeError(f"{consumer['transfer']} is not a registered transfer schema")
        transferer = Transfers[consumer['transfer']](consumer['host'], consumer['port'], consumer['endpoint'])

        consumer = Consumer(connector, actuators, encoder, transferer)
        consumer.run()


if __name__ == "__main__":
    main()
