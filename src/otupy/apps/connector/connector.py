"""The connector."""
from argparse import ArgumentParser
from configparser import ConfigParser
from glob import glob
from os.path import dirname

# noinspection PyUnusedImports
import otupy.actuators  # Do not remove! It is necessary to find the registered actuators.
from otupy import Actuators
from otupy import Consumer
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer


def main() -> None:
    """The main function."""
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
    transfer = config["connector"].getint("transfer")
    encoding = config["connector"].getint("encoding")
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

    # noinspection PyTypeChecker
    consumer = Consumer("connector", actuators, JSONEncoder(), HTTPTransfer(ip, port, endpoint))
    consumer.run()


if __name__ == "__main__":
    main()
