"""The connector."""
from argparse import ArgumentParser
from configparser import ConfigParser
from glob import glob
from os.path import dirname

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
    arguments.add_argument("-c", "--config", default=f"{dirname(__file__)}/connector.ini",
                           help="path to the configuration file")
    args = arguments.parse_args()

    # Parse the configuration file.
    config = ConfigParser()
    config.read(args.config)
    ip = config["connector"].get("ip")
    port = config["connector"].getint("port")
    endpoint = config["connector"].get("endpoint")
    protocol = config["connector"].getint("protocol")
    transfer = config["connector"].get("transfer")
    encoding = config["connector"].get("encoding")
    hostname = config["connector"].get("hostname")
    configs = config["connector"].get("configs")

    actuators = {}
    for file in glob(f"{configs}/**/*.ini", recursive=True):
        actuator_config = ConfigParser()
        actuator_config.read(file)
        for name in actuator_config.sections():
            print(f"Loading {name}...")
            identifier = actuator_config[name].get("id")
            if identifier not in Actuators:
                raise RuntimeError(f"{identifier} is not a registered actuator")
            clazz = Actuators[identifier]
            parameters = {
                "asset_id": name,
                "ip": ip,
                "port": port,
                "endpoint": endpoint,
                "protocol": protocol,
                "transfer": transfer,
                "encoding": encoding,
                "hostname": hostname
            }
            profile = actuator_config[name].get("profile")
            for key in actuator_config[name]:
                if key in ("id", "profile"):
                    continue
                value = None
                try:
                    value = actuator_config[name].getint(key)
                except ValueError:
                    pass
                try:
                    if value is None:
                        value = actuator_config[name].getboolean(key)
                except ValueError:
                    pass
                try:
                    if value is None:
                        value = actuator_config[name].get(key)
                except ValueError:
                    pass
                if value == "None":
                    value = None
                parameters[key] = value
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
