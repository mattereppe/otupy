import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.web import WebSiteManagementClient
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
from otupy.types.data.l4_protocol import L4Protocol
from otupy.profiles.ctxd.data.name import Name
from otupy import ArrayOf

class CTXDActuator_azure(CTXDActuator):
    """
    Azure Context Discovery Actuator
    Collects VMs, Load Balancers, NSGs, Firewalls, App Gateways, App Services, SQL, Storage.
    """
    def is_available(self):
        return True
    def __init__(self, subscription_id=None, domain=None, asset_id=None, hostname=None,
                 ip=None, port=443, protocol="TCP", endpoint=None, transfer="sync", encoding="json"):

        self.subscription_id = subscription_id
        self.domain = domain
        self.asset_id = asset_id
        self.hostname = hostname
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.endpoint = endpoint
        self.transfer = transfer
        self.encoding = encoding

        # Azure credentials
        self.credential = DefaultAzureCredential()
        if not self.subscription_id:
            self.subscription_id = self.get_default_subscription()

        # Azure clients
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
        self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
        self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
        self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)

        # Discover resources and build services
        self.my_links = self.discover_resources()
        self.my_services = self.build_services()

    def get_default_subscription(self):
        """Get default subscription from Azure"""
        sub_client = SubscriptionClient(self.credential)
        return next(sub_client.subscriptions.list()).subscription_id

    def create_consumer(self, resource_name):
        """Create a Consumer object for a resource"""
        return Consumer(
            server=Server(Hostname(resource_name)),
            port=self.port,
            protocol=L4Protocol(self.protocol),
            endpoint=self.endpoint,
            transfer=Transfer(self.transfer),
            encoding=Encoding(self.encoding)
        )

    def add_link(self, links, resource_id, resource_name, role, link_type):
        """Helper to append a Link with a Peer"""
        peer = Peer(
            service_name=Name(resource_name),
            role=PeerRole(role),
            consumer=self.create_consumer(resource_name)
        )
        links.append(Link(name=Name(resource_id), link_type=LinkType(link_type), peers=ArrayOf(Peer)([peer])))

    def discover_resources(self):
        """Discover Azure resources and create links"""
        links = ArrayOf(Link)()

        # --- Virtual Machines ---
        for vm in self.compute_client.virtual_machines.list_all():
            os_name = vm.storage_profile.os_disk.os_type if vm.storage_profile.os_disk else "Unknown"
            self.add_link(links, vm.id, vm.name, role=9, link_type=4)  # control link

        # --- Load Balancers ---
        for lb in self.network_client.load_balancers.list_all():
            self.add_link(links, lb.id, lb.name, role=4, link_type=3)  # packet_flow

        # --- Network Security Groups ---
        for nsg in self.network_client.network_security_groups.list_all():
            self.add_link(links, nsg.id, nsg.name, role=3, link_type=5)  # protect

        # --- Firewalls ---
        for fw in self.network_client.azure_firewalls.list_all():
            self.add_link(links, fw.id, fw.name, role=3, link_type=5)  # protect

        # --- Application Gateways ---
        for app_gw in self.network_client.application_gateways.list_all():
            self.add_link(links, app_gw.id, app_gw.name, role=8, link_type=3)  # packet_flow

        # --- Storage Accounts ---
        for sa in self.storage_client.storage_accounts.list():
            self.add_link(links, sa.id, sa.name, role=5, link_type=2)  # hosting

        # --- App Services ---
        for site in self.web_client.web_apps.list():
            self.add_link(links, site.id, site.name, role=6, link_type=2)  # hosting

        # --- SQL Servers ---
        for sql in self.sql_client.servers.list():
            self.add_link(links, sql.id, sql.name, role=7, link_type=2)  # hosting

        return links

    def build_services(self):
        """Build the main Azure cloud service with discovered links"""
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
        """Return a list of names for discovered links"""
        return ArrayOf(Name)([link.name.obj for link in links])
