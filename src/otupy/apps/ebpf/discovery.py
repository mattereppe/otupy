#!/usr/bin/env python3

from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from posixpath import dirname
import sys
import yaml
from jsonschema import validate, ValidationError

from otupy.apps.ebpf.producer_manager import (
    create_producer,
    load_program,
    query_programs,
    delete_program
)

# ==========================================================
# SECURITY SCHEMA
# ==========================================================

SCHEMA = {
    "type": "object",
    "required": ["consumer", "asset_id", "actions"],
    "additionalProperties": False,
    "properties": {
        "consumer": {
            "type": "object",
            "required": ["host", "port"],
            "additionalProperties": False,
            "properties": {
                "host": {
                    "type": "string",
                    "minLength": 1
                },
                "port": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 65535
                }
            }
        },
        "asset_id": {
            "type": "string",
            "minLength": 1
        },
        "actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type"],
                "additionalProperties": False,
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["load", "delete", "query"]
                    },
                    "program": {
                        "type": "string",
                        "minLength": 1
                    },
                    "interface": {
                        "type": "string",
                        "minLength": 1
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["ingress", "egress", "both"]
                    },
                    "attach_type": {
                        "type": "string",
                        "enum": ["tc", "xdp"]
                    }
                }
            }
        }
    }
}

# ==========================================================
# LOGICAL VALIDATION
# ==========================================================

def validate_action_logic(config: dict):
    """
    Enforce semantic rules:
    - load/delete require program, interface, direction, attach_type
    - query must NOT contain extra parameters
    """

    for i, action in enumerate(config["actions"]):
        action_type = action["type"]

        if action_type in ["load", "delete"]:
            required_fields = ["program", "interface", "direction", "attach_type"]
            for field in required_fields:
                if field not in action:
                    raise ValueError(
                        f"Action[{i}] ({action_type}) missing required field: {field}"
                    )

        if action_type == "query":
            extra_fields = set(action.keys()) - {"type"}
            if extra_fields:
                raise ValueError(
                    f"Action[{i}] (query) must not define extra fields: {extra_fields}"
                )

# ==========================================================
# EXECUTION
# ==========================================================

def run_from_config(config_path: str):

    # ---- Load YAML ----
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"FATAL: Cannot read config file: {e}")
        sys.exit(2)

    # ---- Schema Validation ----
    try:
        validate(instance=config, schema=SCHEMA)
    except ValidationError as e:
        print("\nCONFIG VALIDATION FAILED")
        print(f"Error: {e.message}")
        sys.exit(3)

    # ---- Logical Validation ----
    try:
        validate_action_logic(config)
    except ValueError as e:
        print("\nCONFIG LOGIC VALIDATION FAILED")
        print(f"Error: {e}")
        sys.exit(4)

    # ---- Extract Required Fields (No Defaults Allowed) ----
    host = config["consumer"]["host"]
    port = config["consumer"]["port"]
    asset_id = config["asset_id"]

    print(f"Connecting to {host}:{port}")
    producer = create_producer(host=host, port=port)

    # ---- Execute Actions ----
    for action in config["actions"]:
        action_type = action["type"]
        print(f"\nExecuting action: {action_type}")

        try:
            if action_type == "load":
                load_program(
                    producer,
                    asset_id=asset_id,
                    program_path=action["program"],
                    iface=action["interface"],
                    direction=action["direction"],
                    attach_type=action["attach_type"]
                )

            elif action_type == "delete":
                delete_program(
                    producer,
                    asset_id=asset_id,
                    program_path=action["program"],
                    iface=action["interface"],
                    direction=action["direction"],
                    attach_type=action["attach_type"]
                )

            elif action_type == "query":
                query_programs(producer, asset_id=asset_id)

            print("Success.")

        except Exception as e:
            print(f"Runtime error during {action_type}: {e}")
            sys.exit(5)




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

    run_from_config(str(config_path))


if __name__ == "__main__":
    main()