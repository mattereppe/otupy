""" Skeleton `Actuator` for CTXD profile - Azure

    This module provides an example to create an `Actuator` for the CTXD profile.
    It discovers Azure VMs and models their relationships in CTXD format.
"""

import os
import logging

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import SubscriptionClient

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.transfer import Transfer
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol

from otupy import ArrayOf, Version
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.link import Link

logger = logging.getLogger(__name__)

OPENC2VERS = Version(1, 0)

MY_IDS = {
    'domain': None,
    'asset_id': None
}

class CTXDActuator_azure(CTXDActuator):
    """ CTXD implementation for Azure """

    my_services: ArrayOf(Service) = None # type: ignore
    my_links: ArrayOf(Link) = None # type: ignore
    domain: str = None
    asset_id: str = None
    hostname: any = None
    ip: any = None
    port: any = None
    protocol: any = None
    endpoint: any = None
    transfer: any = None
    encoding: any = None
    subscription_id: str = None

    compute_client: ComputeManagementClient = None
    network_client: NetworkManagementClient = None

    def __init__(self, domain, asset_id, hostname, ip, port, protocol, endpoint, transfer, encoding, subscription_id=None):
        MY_IDS['domain'] = domain
        MY_IDS['asset_id'] = asset_id
        self.domain = domain
        self.asset_id = asset_id
        self.hostname = hostname
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.endpoint = endpoint
        self.transfer = transfer
        self.encoding = encoding
        self.subscription_id = subscription_id

        self.connect_to_azure()
        self.my_links = self.get_links()
        self.my_services = self.get_services()

    def connect_to_azure(self):
        """ Connect to Azure using DefaultAzureCredential """
        try:
            credential = DefaultAzureCredential()

            if not self.subscription_id:
                # Get default subscription
                sub_client = SubscriptionClient(credential)
                self.subscription_id = next(sub_client.subscriptions.list()).subscription_id
            # todo aggiungere controlllo errore
            self.compute_client = ComputeManagementClient(credential, self.subscription_id)
            self.network_client = NetworkManagementClient(credential, self.subscription_id)

            logger.info(f"Connected to Azure subscription {self.subscription_id}")
        except Exception as e:
            logger.error(f"Azure connection failed: {e}")
            raise

    def get_services(self):
        """ Return the Azure cloud as a CTXD Service """
        azure_cloud = Cloud(description="Azure cloud", id=self.subscription_id, name="azure", type="public")

        azure_service = Service(
            name=Name("azure"),
            type=ServiceType(azure_cloud),
            links=self.get_name_links(self.my_links),
            subservices=None,
            owner=self.asset_id,
            release=None,
            security_functions=None,
            actuator=Consumer(
                server=Server(Hostname(self.hostname)),
                port=self.port,
                protocol=L4Protocol(self.protocol),
                endpoint=self.endpoint,
                transfer=Transfer(self.transfer),
                encoding=Encoding(self.encoding),
            )
        )
        return ArrayOf(Service)([azure_service])

    def get_links(self):
        """ Discover Azure VMs and model control links """
        links = ArrayOf(Link)()

        try:
            """Retrieve all virtual_machines"""
            vms = self.compute_client.virtual_machines.list_all()

            for vm in vms:
                vm_id = vm.id
                vm_name = vm.name
                os_profile = getattr(vm, "os_profile", None)
                os_name = os_profile.os_type if os_profile else "unknown"

                tmp_vm = VM(
                    description="azure-vm",
                    id=vm_id,
                    hostname=Hostname(vm_name),
                    os=OS(name=os_name)
                )

                tmp_peer = Peer(
                    service_name=Name(f"vm\n{vm_name}"),
                    role=PeerRole(9),  # VM is controlled by Azure
                    consumer=Consumer(
                        server=Server(Hostname(vm_name)),
                        port=self.port,
                        protocol=L4Protocol(self.protocol),
                        endpoint=self.endpoint,
                        transfer=Transfer(self.transfer),
                        encoding=Encoding(self.encoding),
                    )
                )

                links.append(Link(name=Name(vm_name), link_type=LinkType(4), peers=ArrayOf(Peer)([tmp_peer])))

            # attach a dummy NSG
            nsg_peer = Peer(
                service_name=Name("nsg"),
                role=PeerRole(3),  # hosted by Azure
                consumer=Consumer(
                    server=Server(Hostname("azure-nsg")),
                    port=self.port,
                    protocol=L4Protocol(self.protocol),
                    endpoint=self.endpoint,
                    transfer=Transfer(self.transfer),
                    encoding=Encoding(self.encoding),
                )
            )
            links.append(Link(name=Name("azure-nsg"), link_type=LinkType(2), peers=ArrayOf(Peer)([nsg_peer])))

        except Exception as e:
            logger.error(f"Failed to list Azure VMs: {e}")

        return links

    def get_name_links(self, links):
        """ Extract only the names of the links """
        name_links = ArrayOf(Name)()
        for link in links:
            name_links.append(link.name.obj)
        return name_links