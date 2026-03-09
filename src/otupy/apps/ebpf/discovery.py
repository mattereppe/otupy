#!/usr/bin/env python3
import os
from posixpath import dirname
import sys
from pathlib import Path
from argparse import ArgumentParser
import yaml
from jsonschema import validate



from otupy.profiles.ebpf.targets.TCHook.eBPF_load_TCprogram import eBPF_load_TCprogram
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.apps.ebpf.obsolete.producer_manager import create_producer
import yaml
from jsonschema import validate

from otupy.apps.ebpf.plugin_registry import ProducerPluginRegistry
import otupy.apps.ebpf.plugins as plugins
from otupy.apps.ebpf.plugin_loader import load_plugins

SCHEMA = {
    # same schema you already have
}

def validate_action_logic(config: dict):
    # same as your current function
    pass
def run_from_config(config_path: str):



    # 1️ Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 2 Validate
    validate(instance=config, schema=SCHEMA)
    validate_action_logic(config)

    host = config["consumer"]["host"]
    port = config["consumer"]["port"]
    asset_id = config["asset_id"]

    #  Create a producer (single interface)
    producer = create_producer(host=host, port=port)


    plugin_cls = ProducerPluginRegistry.get("tc")
    plugin = plugin_cls()
    producer = create_producer(host=host, port=port)
    
    
    for action in config["actions"]:
        # The producer will internally:
        #   - determine the right plugin/actuator from action['attach_type']
        #   - determine the right target class (TC/XDP/Kprobe/etc)
        #   - handle load/delete/query
        try:
            program_path=action["program"]
            iface=action["interface"]
            direction=action["direction"]
            attach_type=action["attach_type"]
            full_path = os.path.abspath(program_path)
            prog = ProgramFile(full_path, Section="main")
            direction_obj = Direction(direction)
            attach_obj = AttachType(attach_type)
            target_features = eBPF_load_TCprogram(
                file=prog,
                direction=direction_obj,
                attach_type=attach_obj,
                interface=iface
            )
            parsed = plugin.load(producer, target=target_features, asset_id=asset_id)
            print(f"Action {action['type']} succeeded: {parsed}")
        except Exception as e:
            print(f"Action {action['type']} failed: {e}")

def main():
    
    default_config = f"{dirname(__file__)}/discovery.yaml"

    parser = ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        default=default_config,
        help=f"Path to YAML config file (default: {default_config})"
    )

    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        print(f"FATAL: Config file does not exist: {config_path}")
        sys.exit(1)

    print(f"Using config: {config_path}")
    run_from_config(Path(args.config))

if __name__ == "__main__":
    main()

