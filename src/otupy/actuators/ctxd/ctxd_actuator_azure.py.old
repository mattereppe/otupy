import os
import logging
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
# Import LinkType and PeerRole for type safety and access to constants
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
from otupy.types.data.ipv4_addr import IPv4Addr
from otupy import ArrayOf

logger = logging.getLogger(__name__)

class CTXDActuatorAzure(CTXDActuator):
    """
    OpenC2 Context Discovery Actuator for Azure, modeling Azure resources 
    as Services, Links, and Peers for the CTXD profile.
    """
    def is_available(self):
        """Checks if the actuator is available."""
        return True

    def __init__(self, tenant_id, client_id, client_secret, subscription_id=None,
                 domain=None, asset_id=None, hostname=None,
                 ip=None, port=8080, protocol="TCP", endpoint=None,
                 transfer="1", encoding="1"):
        """
        Initializes the Azure Actuator with credentials and performs initial discovery.
        """
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

        # Initialize Azure management clients
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
        """Fetches the default subscription ID."""
        sub_client = SubscriptionClient(self.credential)
        try:
            return next(sub_client.subscriptions.list()).subscription_id
        except StopIteration:
            raise ValueError("No Azure subscriptions found for the provided credentials.")

    def get_compliant_hostname(self, resource_name):
        """Converts resource name to an RFC 1123 compliant hostname."""
        safe_name = resource_name.replace('_', '-').lower()
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        safe_name = safe_name.strip('-')
        
        if not safe_name:
            return "azure-host-default"
        
        return safe_name[:63]

    def create_consumer(self, resource_name, resource_ip=None):
        """
        Creates a Consumer object using an RFC 1123 compliant hostname or IPv4 address.
        
        Args:
            resource_name (str): The name of the resource.
            resource_ip (str, optional): The private IP address of the resource.
            
        Returns:
            Consumer: The OpenC2 Consumer object.
        """
        
        # Choose whether to use IPv4Addr or Hostname for the Server object (Choice)
        if resource_ip:
            # If the IP is present, use it as the Server(IPv4Addr) choice
            server_peer = Server(IPv4Addr(resource_ip))
        else:
            # Otherwise, use the Hostname Server(Hostname)
            compliant_hostname = self.get_compliant_hostname(resource_name)
            server_peer = Server(Hostname(compliant_hostname))
            
        return Consumer(
            server=server_peer,
            port=self.port,
            protocol=L4Protocol(self.protocol),
            endpoint=self.endpoint,
            transfer=Transfer(self.transfer),
            encoding=Encoding(self.encoding)
        )
        
    def _get_resource_group_name(self, resource_id):
        """Extracts the Resource Group name from the Azure Resource ID."""
        if resource_id and 'resourcegroups' in resource_id.lower():
            # ID format: /subscriptions/{SUB}/resourceGroups/{RG_NAME}/providers/...
            try:
                id_parts = resource_id.split('/')
                rg_index = id_parts.index('resourceGroups') + 1
                return id_parts[rg_index] if rg_index < len(id_parts) else None
            except ValueError:
                return None
        return None

    # --- Wrapper Methods for RG-Scoped Listing ---
    def _list_all_rg_scoped(self, list_func):
        """Wrapper to call resource-group-scoped list functions across all RGs."""
        all_resources = []
        resource_groups = self.resource_client.resource_groups.list()
        
        for rg in resource_groups:
            try:
                # Resources is an iterable, extend the list with its elements
                resources = list_func(rg.name)
                all_resources.extend(list(resources))
            except Exception as e:
                logger.warning(f"Failed to list resources via {list_func.__qualname__} in RG {rg.name}: {e}")
                continue
                
        return all_resources
        
    def list_all_virtual_network_gateways(self):
        """Lists all Virtual Network Gateways across all resource groups."""
        return self._list_all_rg_scoped(self.network_client.virtual_network_gateways.list)

    def list_all_local_network_gateways(self):
        """Lists all Local Network Gateways across all resource groups."""
        return self._list_all_rg_scoped(self.network_client.local_network_gateways.list)

    def list_all_storage_accounts(self):
        """Lists all Storage Accounts across all resource groups."""
        return self._list_all_rg_scoped(self.storage_client.storage_accounts.list)

    def list_all_sql_servers(self):
        """Lists all SQL Servers across all resource groups."""
        return self._list_all_rg_scoped(self.sql_client.servers.list)

    def list_all_key_vaults(self):
        """Lists all Key Vaults across all resource groups."""
        return self._list_all_rg_scoped(self.kv_client.vaults.list)

    def list_all_container_registries(self):
        """Lists all Container Registries across all resource groups."""
        return self._list_all_rg_scoped(self.cr_client.registries.list)

    def list_all_compute_disks(self):
        """Lists all Compute Disks across all resource groups."""
        return self._list_all_rg_scoped(self.compute_client.disks.list)

    def list_all_vpn_connections(self):
        """
        Fetches all VPN connections across the subscription by iterating over all 
        Virtual Network Gateways (the parent resources).
        """
        all_connections = []
        vpn_gateways = self.list_all_virtual_network_gateways()
        
        for gateway in vpn_gateways:
            try:
                gateway_name = gateway.name 
                id_parts = gateway.id.split('/')
                resource_group_name = id_parts[4]
                
                connections = self.network_client.vpn_connections.list_by_vpn_gateway(
                    resource_group_name,
                    gateway_name
                )
                all_connections.extend(list(connections))
            except Exception as e:
                logger.warning(f"Failed to list VPN connections for gateway '{gateway.name}': {e}")
                continue
                
        return all_connections

    def list_all_private_dns_zone_groups(self):
        """
        Fetches all Private DNS Zone Groups across the subscription by iterating over 
        all Private Endpoints (the parent resource).
        """
        all_dns_zone_groups = []
        # List all Private Endpoints across the subscription
        private_endpoints = self.network_client.private_endpoints.list_by_subscription() 
        
        for endpoint in private_endpoints:
            try:
                private_endpoint_name = endpoint.name 
                id_parts = endpoint.id.split('/')
                resource_group_name = id_parts[4]
                
                groups = self.network_client.private_dns_zone_groups.list(
                    resource_group_name,
                    private_endpoint_name
                )
                all_dns_zone_groups.extend(list(groups))
                
            except Exception as e:
                logger.warning(f"Failed to list Private DNS Zone Groups for endpoint '{endpoint.name}': {e}")
                continue
                
        return all_dns_zone_groups
    # ---------------------------------------------

    def add_link(self, links, resource_id, resource_name, role, link_type, is_host=True, ip_address=None, resource_group=None, tags=None):
        """
        Adds a Link to the array, ensuring unique Link names (resource_id) and 
        reliable Peer service names. Includes optional IP address, RG and Tags.
        
        Args:
            links (ArrayOf(Link)): The array to append the new Link to.
            resource_id (str): The unique Azure Resource ID (used as Link name).
            resource_name (str): The friendly resource name (used as Peer service_name).
            role (PeerRole): The role of the resource in the relationship.
            link_type (LinkType): The type of relationship.
            is_host (bool, optional): If True, a Consumer is created for the Peer. Defaults to True.
            ip_address (str, optional): The IP address for the Consumer (if is_host=True). Defaults to None.
            resource_group (str, optional): The name of the Resource Group. Defaults to None.
            tags (dict, optional): The resource tags. Defaults to None.
        """
        # 1. Ensure we get a meaningful name for the Peer service
        final_resource_name = resource_name
        if not final_resource_name or final_resource_name == "unknown":
            final_resource_name = self._get_name_from_id(resource_id)

        consumer = None
        if is_host:
            # Pass the IP address to the consumer only if it's a host
            consumer = self.create_consumer(final_resource_name, resource_ip=ip_address) 

        peer = Peer(
            # Use the most reliable name for the human-readable service name
            service_name=Name(final_resource_name), 
            role=PeerRole(role),
            consumer=consumer
        )
        
        # 2. Build description string to include RG and Tags for Producer clustering/context
        description_parts = []
        if resource_group:
            description_parts.append(f"RG:{resource_group}")
        if tags and isinstance(tags, dict):
             # Convert tags dict to a simple string representation
             tag_str = ";".join([f"{k}:{v}" for k, v in tags.items()])
             description_parts.append(f"Tags:{tag_str}")
        description = " ".join(description_parts) if description_parts else None
        
        # CRITICAL: Ensure the Link name is the unique resource ID.
        links.append(Link(
            name=Name(resource_id), 
            link_type=link_type, 
            peers=ArrayOf(Peer)([peer]),
            description=description # Pass RG and Tags via description
        ))

    def _get_name_from_id(self, resource_id):
        """
        Extracts the resource name from the Azure Resource ID, 
        which is necessary when the 'name' attribute is not directly available 
        or is corrupted.
        """
        # ID format ends with: /providers/{PROVIDER}/resources/{RESOURCE_NAME}
        # The resource name is the last segment of the ID.
        if resource_id and resource_id != "unknown":
            return resource_id.split('/')[-1]
        return "unknown_name"

    def discover_resources(self):
        """
        Discovers all relevant Azure resources using the SDK clients and creates 
        OpenC2 CTXD Links for them, classifying them as Host/Endpoint or 
        Boundary/Container resources.
        
        Returns:
            ArrayOf(Link): The list of discovered OpenC2 Links.
        """
        links = ArrayOf(Link)()
        
        # --- HOST/ENDPOINT RESOURCES (is_host=True, require Consumer) ---
        host_discovery_map = [
            (self.compute_client.virtual_machines.list_all, PeerRole.controlled, LinkType.control),      
            (self.compute_client.virtual_machine_scale_sets.list_all, PeerRole.controlled, LinkType.control), 
            (self.network_client.application_gateways.list_all, PeerRole.control, LinkType.control),   
            (self.aks_client.managed_clusters.list, PeerRole.control, LinkType.control),               
            (self.network_client.load_balancers.list_all, PeerRole.host, LinkType.hosting),        
            (self.list_all_virtual_network_gateways, PeerRole.ingress, LinkType.hosting), 
            (self.list_all_local_network_gateways, PeerRole.ingress, LinkType.hosting),   
            (self.list_all_vpn_connections, PeerRole.ingress, LinkType.hosting),
            (self.network_client.private_endpoints.list_by_subscription, PeerRole.ingress, LinkType.hosting), 
            (self.network_client.network_watchers.list_all, PeerRole.ingress, LinkType.hosting),      
            (self.web_client.web_apps.list, PeerRole.egress, LinkType.api),                      
            (self.list_all_storage_accounts, PeerRole.ingress, LinkType.api),           
            (self.list_all_sql_servers, PeerRole.both, LinkType.api),                
            (self.list_all_key_vaults, PeerRole.both, LinkType.api),                 
            (self.list_all_container_registries, PeerRole.egress, LinkType.api),       
            (self.msi_client.user_assigned_identities.list_by_subscription, PeerRole.both, LinkType.api), 
            (self.comm_client.communication_services.list_by_subscription, PeerRole.both, LinkType.api), 
            (self.comm_client.email_services.list_by_subscription, PeerRole.both, LinkType.api),  
        ]

        # --- BOUNDARY/CONTAINER RESOURCES (is_host=False, omit Consumer) ---
        boundary_discovery_map = [
            (self.network_client.virtual_networks.list_all, PeerRole.ingress, LinkType.hosting),       
            (self.network_client.network_interfaces.list_all, PeerRole.ingress, LinkType.hosting), 
            (self.list_all_private_dns_zone_groups, PeerRole.ingress, LinkType.hosting),    
            (self.network_client.network_security_groups.list_all, PeerRole.guest, LinkType.protect), 
            (self.network_client.azure_firewalls.list_all, PeerRole.guest, LinkType.protect),        
            (self.list_all_compute_disks, PeerRole.ingress, LinkType.packet_flow),
        ]

        # 1. Discover Host/Endpoint Resources
        for list_func, role, link_type in host_discovery_map:
            try:
                for resource in list_func():
                    resource_id = getattr(resource, "id", "unknown")
                    resource_name = getattr(resource, "name", "unknown")
                    resource_group = self._get_resource_group_name(resource_id)
                    resource_tags = getattr(resource, "tags", None) # Extract tags
                    
                    self.add_link(links, resource_id, resource_name, role, link_type, 
                                  is_host=True, resource_group=resource_group, tags=resource_tags)
            except Exception as e:
                logger.error(f"Error during host discovery for {list_func.__qualname__}: {e}")
                # Re-raise the error to prevent execution if the host part fails
                raise e 

        # 2. Discover Boundary/Container Resources
        for list_func, role, link_type in boundary_discovery_map:
            try:
                for resource in list_func():
                    resource_id = getattr(resource, "id", "unknown")
                    resource_name = getattr(resource, "name", "unknown")
                    resource_group = self._get_resource_group_name(resource_id)
                    resource_tags = getattr(resource, "tags", None)

                    is_host_flag = False
                    ip_address_to_use = None
                    
                    # IP EXTRACTION LOGIC for Network Interface (NIC)
                    if list_func == self.network_client.network_interfaces.list_all:
                        if getattr(resource, "ip_configurations", None) and resource.ip_configurations:
                            private_ip = getattr(resource.ip_configurations[0], "private_ip_address", None)
                            if private_ip:
                                is_host_flag = True # The NIC becomes a host (and will have a consumer)
                                ip_address_to_use = private_ip
                    
                    # Add the parent resource 
                    self.add_link(links, resource_id, resource_name, role, link_type, 
                                  is_host=is_host_flag, ip_address=ip_address_to_use, 
                                  resource_group=resource_group, tags=resource_tags)
                    
                    # LOGIC ADDITION: NSG Rule Expansion
                    if list_func == self.network_client.network_security_groups.list_all:
                        try:
                            nsg_rules = self.list_nsg_rules(resource_id)
                            for rule in nsg_rules:
                                rule_name = (
                                    f"{resource_name} Rule: P{rule.priority} {rule.access.upper()} "
                                    f"{rule.direction.upper()} {rule.protocol}/{rule.destination_port_range}"
                                )
                                rule_id = f"{resource_id}/securityRules/{rule.name}"
                                
                                # NSG Rules do not have tags but use the parent's RG
                                self.add_link(links, rule_id, rule_name, PeerRole.guest, LinkType.protect, 
                                              is_host=False, resource_group=resource_group) 
                                
                                self._add_parent_child_link(links, resource_id, rule_id, rule)

                        except Exception as rule_e:
                            logger.warning(f"Error discovering rules for NSG {resource_name}: {rule_e}")
                            
            except Exception as e:
                logger.error(f"Error during boundary discovery for {list_func.__qualname__}: {e}")
                raise e 
        
        unique_links = {}
        for link in links:
            # Use the Link name (resource_id) as the key
            unique_links[link.name.obj] = link 
            
        # CRITICAL CALL: Adds logical connection links (VM->NIC, NIC->NSG)
        connection_links = self.discover_connections(list(unique_links.values()))
        for link in connection_links:
            # Connection links have names based on resource names, not IDs, so they do not overlap
            unique_links[link.name.obj] = link

        return ArrayOf(Link)(list(unique_links.values()))
            
    def list_nsg_rules(self, nsg_id):
        """
        Fetches all security rules (inbound and outbound) for a given NSG resource ID.
        
        Args:
            nsg_id (str): The Azure Resource ID of the NSG.
            
        Returns:
            list: A list of Azure SecurityRule objects.
        """
        # Extract Resource Group name and NSG name from the resource ID
        id_parts = nsg_id.split('/')
        if len(id_parts) < 9 or id_parts[3].lower() != 'resourcegroups' or id_parts[7].lower() != 'networksecuritygroups':
            logger.error(f"Invalid NSG resource ID format: {nsg_id}")
            return []

        resource_group_name = id_parts[4]
        nsg_name = id_parts[8]
        
        try:
            rules = self.network_client.security_rules.list(
                resource_group_name,
                nsg_name
            )
            return list(rules)
        except Exception as e:
            logger.error(f"Failed to list security rules for NSG '{nsg_name}' in RG '{resource_group_name}': {e}")
            return []
            
    def discover_connections(self, existing_links):
        """
        Correlates discovered resources (e.g., VMs to NSGs via NICs) 
        and adds explicit connection links.
        
        Args:
            existing_links (list): The list of links already discovered by ID.
            
        Returns:
            ArrayOf(Link): The list of new logical connection links.
        """
        new_links = ArrayOf(Link)()
        
        # Dictionary of Resource ID -> Name for quick lookup
        resource_id_to_name = {link.name.obj: self._get_name_from_id(link.name.obj) for link in existing_links}
        
        # 1. Find NIC -> NSG connections
        try:
            for nic in self.network_client.network_interfaces.list_all():
                nic_id = getattr(nic, "id", None)
                nic_name = getattr(nic, "name", "unknown")
                
                # Get the NSG connected to the NIC
                nsg_ref = getattr(nic, "network_security_group", None)
                if nsg_ref:
                    nsg_id = getattr(nsg_ref, "id", None)
                    if nsg_id and nic_id:
                        nsg_name = resource_id_to_name.get(nsg_id, self._get_name_from_id(nsg_id))
                        
                        # Add the NIC -> NSG protection link
                        link_name = f"{nic_name}_protected_by_{nsg_name}"
                        
                        peer_nic = Peer(service_name=Name(nic_name), role=PeerRole.controlled, consumer=None)
                        peer_nsg = Peer(service_name=Name(nsg_name), role=PeerRole.control, consumer=None)
                        
                        new_links.append(Link(
                            name=Name(link_name), 
                            link_type=LinkType.protect, 
                            peers=ArrayOf(Peer)([peer_nic, peer_nsg])
                        ))
        except Exception as e:
            logger.warning(f"Failed to discover NIC-NSG connections: {e}")


        # 2. Find VM -> NIC connections
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                vm_id = getattr(vm, "id", None)
                vm_name = getattr(vm, "name", "unknown")
                
                nic_refs = getattr(vm, "network_profile", {}).get("network_interfaces", [])
                for nic_ref in nic_refs:
                    nic_id = getattr(nic_ref, "id", None)
                    if nic_id and vm_id:
                        nic_name = resource_id_to_name.get(nic_id, self._get_name_from_id(nic_id))

                        # Add the VM -> NIC connection link
                        link_name = f"{vm_name}_connected_to_{nic_name}"

                        peer_vm = Peer(service_name=Name(vm_name), role=PeerRole.host, consumer=None)
                        peer_nic = Peer(service_name=Name(nic_name), role=PeerRole.guest, consumer=None)

                        new_links.append(Link(
                            name=Name(link_name), 
                            link_type=LinkType.packet_flow, # Use packet_flow for the physical connection
                            peers=ArrayOf(Peer)([peer_vm, peer_nic])
                        ))
        except Exception as e:
            logger.warning(f"Failed to discover VM-NIC connections: {e}")
        
        return new_links 

    def _add_parent_child_link(self, links, parent_id, child_id, rule_object):
        """
        Adds a Link to model the parent-child relationship between an NSG and its rule.
        
        Args:
            links (ArrayOf(Link)): The array to append the new Link to.
            parent_id (str): The Azure Resource ID of the parent (e.g., NSG).
            child_id (str): The Azure Resource ID of the child (e.g., Security Rule).
            rule_object (SecurityRule): The rule object (unused but kept for context).
        """
        # Create a specific Link name for this parent-child relationship (the arc)
        link_name = f"{self._get_name_from_id(parent_id)}_contains_{self._get_name_from_id(child_id)}"
        
        # Create Peers
        peer_parent = Peer(
            service_name=Name(self._get_name_from_id(parent_id)),
            role=PeerRole.host,  # The NSG is the host/container
            consumer=None        
        )
        peer_child = Peer(
            service_name=Name(self._get_name_from_id(child_id)),
            role=PeerRole.guest, # The Rule is the contained resource
            consumer=None
        )
        
        links.append(Link(
            name=Name(link_name), 
            link_type=LinkType.protect, # Use a security-related link type
            peers=ArrayOf(Peer)([peer_parent, peer_child])
        ))

    def build_services(self):
        """
        Builds the root OpenC2 Service for Azure and wraps all discovered Links.
        
        Returns:
            ArrayOf(Service): The list containing the root Azure Service.
        """
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
        """
        Converts an ArrayOf(Link) to an ArrayOf(Name) containing just the link names.
        """
        return ArrayOf(Name)([link.name.obj for link in links])