import os
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.msi import ManagedServiceIdentityClient
from azure.mgmt.communication import CommunicationServiceManagementClient
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.transfer import Transfer
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.link import Link
from otupy.types.data.hostname import Hostname
from otupy.profiles.ctxd.data.name import Name
from otupy.types.data.l4_protocol import L4Protocol
from otupy import ArrayOf

class CTXDActuatorAzure(CTXDActuator):
    def is_available(self):
        return True

    def __init__(self, tenant_id, client_id, client_secret, subscription_id=None,
                 domain=None, asset_id=None, hostname=None,
                 ip=None, port=8080, protocol="TCP", endpoint=None,
                 transfer="1", encoding="1"):

        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        self.asset_id = asset_id
        self.hostname = hostname
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.endpoint = endpoint
        self.transfer = transfer
        self.encoding = encoding

        self.credential = ClientSecretCredential(tenant_id, client_id, client_secret)

        if not self.subscription_id:
            self.subscription_id = self.get_default_subscription()

        # Azure clients
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
        self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
        self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
        self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)
        self.kv_client = KeyVaultManagementClient(self.credential, self.subscription_id)
        self.cr_client = ContainerRegistryManagementClient(self.credential, self.subscription_id)
        self.aks_client = ContainerServiceClient(self.credential, self.subscription_id)
        self.msi_client = ManagedServiceIdentityClient(self.credential, self.subscription_id)
        self.comm_client = CommunicationServiceManagementClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)

        self.my_links = self.discover_resources()
        self.my_services = self.build_services()

    def get_default_subscription(self):
        sub_client = SubscriptionClient(self.credential)
        return next(sub_client.subscriptions.list()).subscription_id

    def create_consumer(self, resource_name):
        return Consumer(
            server=Server(Hostname(resource_name)),
            port=self.port,
            protocol=L4Protocol(self.protocol),
            endpoint=self.endpoint,
            transfer=Transfer(self.transfer),
            encoding=Encoding(self.encoding)
        )

    def add_link(self, links, resource_id, resource_name, role, link_type):
        peer = Peer(
            service_name=Name(resource_name),
            role=PeerRole(role),
            consumer=self.create_consumer(resource_name)
        )
        links.append(Link(name=Name(resource_id), link_type=LinkType(link_type), peers=ArrayOf(Peer)([peer])))

    def discover_resources(self):
        links = ArrayOf(Link)()

        discovery_map = [
            (self.compute_client.virtual_machines.list_all, 9, 4),
            (self.compute_client.virtual_machine_scale_sets.list, 9, 4),
            (self.network_client.load_balancers.list_all, 4, 3),
            (self.network_client.network_security_groups.list_all, 3, 5),
            (self.network_client.application_gateways.list_all, 8, 3),
            (self.network_client.azure_firewalls.list_all, 3, 5),
            (self.network_client.virtual_networks.list_all, 5, 2),
            (self.network_client.virtual_network_gateways.list, 5, 2),
            (self.network_client.local_network_gateways.list, 5, 2),
            (self.network_client.vpn_connections.list_by_vpn_gateway, 5, 2),
            (self.network_client.private_endpoints.list_by_subscription, 5, 2),
            (self.network_client.network_interfaces.list_all, 5, 2),
            (self.network_client.network_watchers.list_all, 5, 2),
            (self.network_client.private_dns_zone_groups.list, 5, 2),
            (self.network_client.virtual_networks.list_all, 5, 2),
            (self.storage_client.storage_accounts.list, 5, 2),
            (self.web_client.web_apps.list, 6, 2),
            (self.sql_client.servers.list, 7, 2),
            (self.kv_client.vaults.list, 7, 2),
            (self.cr_client.registries.list, 6, 2),
            (self.aks_client.managed_clusters.list, 8, 3),
            (self.msi_client.user_assigned_identities.list_by_subscription, 7, 2),
            (self.comm_client.communication_services.list_by_subscription, 7, 2),
            (self.comm_client.email_services.list_by_subscription, 7, 2),
            (self.compute_client.disks.list, 5, 2)
        ]

        for list_func, role, link_type in discovery_map:
            try:
                for resource in list_func():
                    self.add_link(links, getattr(resource, "id", "unknown"), getattr(resource, "name", "unknown"), role, link_type)
            except Exception:
                continue

#        print("=== Risorse visibili con questo Service Principal ===")
 #       for link in links:
  #          print(f"- {link.peers[0].service_name.obj} ({link.name.obj})")

        return links

    def build_services(self):
        cloud_service = Cloud(description="Azure Cloud", id=self.subscription_id, name="azure", type="cloud")
        azure_service = Service(
            name=Name("azure"),
            type=ServiceType(cloud_service),
            links=self.get_name_links(self.my_links),
            subservices=None,
            owner=self.asset_id,
            release=None,
            security_functions=None,
            actuator=self.create_consumer(self.hostname)
        )
        return ArrayOf(Service)([azure_service])

    @staticmethod
    def get_name_links(links):
        return ArrayOf(Name)([link.name.obj for link in links])
