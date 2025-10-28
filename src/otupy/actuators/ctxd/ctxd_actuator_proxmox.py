import logging
from proxmoxer import ProxmoxAPI
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.transfer import Transfer
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.vm import VM
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.os import OS
from otupy.types.data.l4_protocol import L4Protocol
from otupy.types.data.hostname import Hostname
from otupy.types.base.array_of import ArrayOf

logger = logging.getLogger(__name__)

class CTXDActuator_Proxmox(CTXDActuator):
    
    # --- Initialization and Connection ---
    def is_available(self):
        return True
    
    def __init__(self, domain, asset_id, hostname, ip, port, protocol, endpoint, transfer, encoding,
                 proxmox_host, username, password, verify_ssl=False):
        self.domain = domain
        self.asset_id = asset_id
        self.hostname = hostname
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.endpoint = endpoint
        self.transfer = transfer
        self.encoding = encoding
        self.proxmox_host = proxmox_host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.proxmox = None
        self.my_services = ArrayOf(Service)()
        self.my_links = ArrayOf(Link)()
        
        self.connect_to_proxmox()
        self.my_links = self.discover_links()
        self.my_services = self.discover_services()

    def connect_to_proxmox(self):
        try:
            self.proxmox = ProxmoxAPI(
                self.proxmox_host,
                user=self.username,
                password=self.password,
                verify_ssl=self.verify_ssl
            )
            logger.info(f"Connected to Proxmox host: {self.proxmox_host} successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox at {self.proxmox_host}: {e}")
            raise

    # --- Discovery Methods ---
    def discover_links(self):
        links = ArrayOf(Link)()
        try:
            nodes_list = self.proxmox.nodes.get()
            
            if not nodes_list:
                 logger.warning("No Proxmox nodes found.")
                 return links

            for node in nodes_list:
                node_name = node['node']
                
                # Discover LXC Containers (CTs)
                for ct in self.proxmox.nodes(node_name).lxc.get():
                    vmid = ct['vmid']
                    
                    # FIX: Safely retrieve and validate the name
                    name_raw = ct.get('name')
                    if not name_raw:
                        logger.warning(f"LXC Container with VMID {vmid} on node {node_name} is missing a name. Skipping.")
                        continue
                        
                    name = str(name_raw) # Ensure name is a string
                    
                    peer = Peer(
                        service_name=Name(f"{name} ({vmid})"),
                        role=PeerRole(9),
                        consumer=Consumer(
                            server=Server(Hostname(name)), 
                            port=self.port,
                            protocol=L4Protocol(self.protocol),
                            endpoint=self.endpoint,
                            transfer=Transfer(self.transfer),
                            encoding=Encoding(self.encoding)
                        )
                    )
                    links.append(Link(name=Name(f"CT-{vmid}"), link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
                    logger.debug(f"Discovered Container Link: {name}")

                # Discover QEMU Virtual Machines (VMs)
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    vmid = vm['vmid']
                    
                    # FIX: Safely retrieve and validate the name
                    name_raw = vm.get('name')
                    if not name_raw:
                        logger.warning(f"QEMU VM with VMID {vmid} on node {node_name} is missing a name. Skipping.")
                        continue
                        
                    name = str(name_raw) # Ensure name is a string
                    
                    peer = Peer(
                        service_name=Name(f"{name} ({vmid})"),
                        role=PeerRole(9),
                        consumer=Consumer(
                            server=Server(Hostname(name)), 
                            port=self.port,
                            protocol=L4Protocol(self.protocol),
                            endpoint=self.endpoint,
                            transfer=Transfer(self.transfer),
                            encoding=Encoding(self.encoding)
                        )
                    )
                    links.append(Link(name=Name(f"VM-{vmid}"), link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
                    logger.debug(f"Discovered VM Link: {name}")

        except Exception as e:
            logger.error(f"Failed to discover Proxmox links: {e}")
        return links

    def get_name_links(self, links):
        """Utility method to extract Name objects from a list of Link objects, safely."""
        name_links = ArrayOf(Name)()
        for link in links:
            # This safety check is crucial for handling previous errors that may have resulted in invalid links
            if link and hasattr(link, 'name') and link.name is not None:
                name_links.append(link.name)
            else:
                logger.warning("Skipping invalid link object during name extraction.")
        return name_links

    def discover_services(self):
        services = ArrayOf(Service)()
        try:
            link_names = self.get_name_links(self.my_links)
            
            # Use the Cloud data type instance for ServiceType, which resolves the 'is not in list' error.
            proxmox_cloud_instance = Cloud(
                description='Proxmox Virtual Environment Hypervisor', 
                id=self.proxmox_host, 
                name=self.hostname
            )
            
            proxmox_service = Service(
                name=Name("proxmox-pve"),
                type=ServiceType(proxmox_cloud_instance), 
                links=link_names,
                owner=self.asset_id,
                actuator=Consumer(
                    server=Server(Hostname(self.hostname)),
                    port=self.port,
                    protocol=L4Protocol(self.protocol),
                    endpoint=self.endpoint,
                    transfer=Transfer(self.transfer),
                    encoding=Encoding(self.encoding)
                )
            )
            services.append(proxmox_service)
            logger.info("Proxmox service created successfully.")
        except Exception as e:
            logger.error(f"Failed to create Proxmox service: {e}")
        return services