import json
import logging
import otupy as oc2
from otupy.actuators.ctxd.ctxd_actuator_docker import CTXDActuator_docker
from otupy.actuators.ctxd.ctxd_actuator_kubernetes import CTXDActuator_kubernetes
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd

from otupy.actuators.ctxd.ctxd_actuator_proxmox import CTXDActuator_Proxmox
from otupy.actuators.ctxd.ctxd_actuator_azure import CTXDActuatorAzure
import os
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))
logger.addHandler(stdout_handler)

CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+"/configuration.json"

def load_config(file_path):

    with open(file_path, "r") as f:
        return json.load(f)

def create_actuator(actuators,conf, consumer_ip, consumer_port, consumer_endpoint):
    actuator_type = conf["type"].lower()

    common_args = dict(
        domain=None,
        asset_id=conf["asset_id"],
        hostname=conf["hostname"],
        ip=consumer_ip,
        port=consumer_port,
        protocol=conf.get("protocol", 6),
        endpoint=consumer_endpoint,
        transfer=conf.get("transfer", 1),
        encoding=conf.get("encoding", 1)
    )
    if actuator_type == "proxmox":
        json_path = os.path.abspath(conf.get("file_secrets"))

        # Load JSON
        with open(json_path, "r") as f:
            secrets = json.load(f)

        # Access secrets
        PROXMOX_HOST = secrets.get("proxmox_host")
        PROXMOX_USERNAME = secrets.get("username")
        PROXMOX_PASSWORD = secrets.get("password")
        return CTXDActuator_Proxmox(
            **common_args,
            proxmox_host=PROXMOX_HOST,
            username=PROXMOX_USERNAME,
            password=PROXMOX_PASSWORD,
            verify_ssl=False
        )
    elif actuator_type == "azure":

        json_path = os.path.abspath(conf.get("file_secrets"))

        # Load JSON
        with open(json_path, "r") as f:
            secrets = json.load(f)

        # Access secrets
        tenant_id = secrets.get("tenant_id")
        client_id = secrets.get("client_id")
        client_secret = secrets.get("client_secret")
        subscription_id = secrets.get("subscription_id")
        return CTXDActuatorAzure(
            **common_args,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            subscription_id=subscription_id

        )
    elif (actuator_type== "kubernetes"):
                #CTXDActuator_kubernetes is able to find the connected VM, containers and namespaces to the kuberenetes cloud
                return CTXDActuator_kubernetes(**common_args,
                                                namespace = conf['namespace'],
                                                config_file =  conf['config_file'],
                                                kube_context =  conf['kube_context'],
                                                actuators=actuators)
            
    elif(actuator_type== "docker"):
        #CTXDActuator_docker is able to find the hosting VM and managed containers
        return CTXDActuator_docker(**common_args, actuators=actuators)
    else:
        raise ValueError(f"Unknown actuator type: {actuator_type}")

def start_consumer():
    config = load_config(CONFIG_FILE)
    consumer_conf = config["consumer"]

    ip = consumer_conf["ip"]
    port = consumer_conf["port"]
    endpoint = consumer_conf["endpoint"]

    actuators = {}
    for cluster_conf in config["clusters"]:
        actuators[(ctxd.Profile.nsid, cluster_conf["type"])] = create_actuator(
            actuators,cluster_conf, ip, port, endpoint
        )

    consumer = oc2.Consumer(
        consumer_conf.get("name", "unified_consumer"),
        actuators=actuators,
        encoder=JSONEncoder(),
        transfer=HTTPTransfer(host=ip, port=port, endpoint=endpoint)
    )

    logger.info("Running consumer with actuators: %s", list(actuators.keys()))
    consumer.run()

if __name__ == "__main__":
    start_consumer()
