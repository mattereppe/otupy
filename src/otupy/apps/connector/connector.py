"""The connector."""

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
from otupy import Consumer


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

        ip = config["ip"]
        port = config["port"]
        endpoint = config["endpoint"]
        transfer = config["transfer"]
        encoding = config["encoding"]
        configs = config["configs"]

        actuators = {}
        for file in glob(f"{configs}/**/*.yaml", recursive=True):
            with open(file) as f:
                data = safe_load(f)
                for name, values in data.items():
                    print(f"Loading {name}...")
                    identifier = values["id"]
                    if identifier not in Actuators:
                        raise RuntimeError(f"{identifier} is not a registered actuator")
                    clazz = Actuators[identifier]
                    parameters = dict(values)
                    del parameters["id"]
                    del parameters["profile"]

                    profile = values["profile"]
                    actuators[(profile, name)] = clazz(**parameters)

        # Load the encoder.
        if encoding not in Encoders.__members__:
            raise RuntimeError(f"{encoding} is not a registered encoding schema")
        encoder = Encoders[encoding]

        # Load the transferer (beautiful name, eh?).
        if transfer not in Transfers:
            raise RuntimeError(f"{transfer} is not a registered transfer schema")
        transferer = Transfers[transfer](ip, port, endpoint)

        consumer = Consumer("connector", actuators, encoder, transferer)
        consumer.run()


if __name__ == "__main__":
    main()
