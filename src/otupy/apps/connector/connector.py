"""The connector."""
from argparse import ArgumentParser
from configparser import ConfigParser
from glob import glob

from otupy import Consumer
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer


def load_class(class_name: str) -> type:
    """
    Dynamically load a class from its fully qualified name.
    :param class_name: Fully qualified name of the class to load.
    :returns: The class object.
    :raises ImportError: If the module cannot be imported.
    :raises AttributeError: If the class does not exist in the module.
    """
    try:
        module_path, class_name = class_name.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        clazz = getattr(module, class_name)

        return clazz
    except ImportError as e:
        # noinspection PyUnboundLocalVariable
        raise ImportError(f"Could not import module {module_path}: {e}")
    except AttributeError as e:
        # noinspection PyUnboundLocalVariable
        raise AttributeError(f"Class {class_name} not found in module {module_path}: {e}")


def main() -> None:
    """The main function."""
    arguments = ArgumentParser()
    arguments.add_argument("-c", "--config", default="connector.ini", help="path to the configuration file")
    args = arguments.parse_args()

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
            clazz = load_class(actuator_config[name].get("class"))
            if not hasattr(clazz, "run"):
                raise RuntimeError(f"The class {clazz} does not have a run method")
            parameters = {
                "asset_id":name,
                "ip":ip,
                "port":port,
                "endpoint":endpoint,
                "protocol":protocol,
                "transfer":transfer,
                "encoding":encoding,
                "hostname":hostname
            }
            profile = actuator_config[name].get("profile")
            for key in actuator_config[name]:
                if key in ("class", "profile"):
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
