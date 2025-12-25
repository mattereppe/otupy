#!/usr/bin/env python3

import os
import json
import logging

import otupy as oc2
import otupy.profiles.ctxd as ctxd
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.actuators.ctxd.ctxd_actuator_azure import CTXDActuatorAzure

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logger = logging.getLogger("azure-consumer")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))
logger.addHandler(handler)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "configuration.json"
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def load_config(path):
    with open(path, "r") as f:
        return json.load(f)

def load_azure_secrets(path):
    with open(os.path.abspath(path), "r") as f:
        return json.load(f)

# --------------------------------------------------
# ACTUATOR CREATION 
# --------------------------------------------------

def create_azure_actuator(conf, consumer_ip, consumer_port, consumer_endpoint):
    secrets = load_azure_secrets(conf["file_secrets"])

    common_args = dict(
        domain=None,
        asset_id=conf["asset_id"],
        hostname=conf["hostname"],
        ip=consumer_ip,
        port=consumer_port,
        protocol=conf.get("protocol", 6),
        endpoint=consumer_endpoint,
        transfer=conf.get("transfer", 1),
        encoding=conf.get("encoding", 1),
    )

    return CTXDActuatorAzure(
        **common_args,
        tenant_id=secrets["tenant_id"],
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        resource_group=secrets["resource_group"],
        cluster_name=secrets["cluster_name"],
    )

# --------------------------------------------------
# CONSUMER
# --------------------------------------------------

def start_consumer():
    config = load_config(CONFIG_FILE)

    consumer_conf = config["consumer"]
    cluster_conf = config["clusters"][0]  # only Azure

    ip = consumer_conf["ip"]
    port = consumer_conf["port"]
    endpoint = consumer_conf["endpoint"]

    azure_actuator = create_azure_actuator(
        cluster_conf,
        ip,
        port,
        endpoint
    )

    actuators = {
        (ctxd.Profile.nsid, "azure"): azure_actuator
    }

    consumer = oc2.Consumer(
        consumer_conf.get("name", "azure_consumer"),
        actuators=actuators,
        encoder=JSONEncoder(),
        transfer=HTTPTransfer(
            host=ip,
            port=port,
            endpoint=endpoint
        )
    )

    logger.info("Starting Azure AKS consumer")
    consumer.run()

# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

if __name__ == "__main__":
    start_consumer()
