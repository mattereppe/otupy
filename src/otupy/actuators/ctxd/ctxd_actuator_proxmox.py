import logging
from proxmoxer import ProxmoxAPI
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.service import Service
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
from otupy.types.data.l4_protocol import L4Protocol
from otupy.types.data.hostname import Hostname
from otupy.types.base.array_of import ArrayOf

logger = logging.getLogger(__name__)

class CTXDActuator_Proxmox(CTXDActuator):
    
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
            logger.info("Connected to Proxmox successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox: {e}")

    def discover_links(self):
        links = ArrayOf(Link)()
        try:
            for node in self.proxmox.nodes.get():
                node_name = node['node']
                for ct in self.proxmox.nodes(node_name).lxc.get():
                    vmid = ct['vmid']
                    name = ct.get('name', f"CT-{vmid}")
                    peer = Peer(
                        service_name=Name(name),
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
                    links.append(Link(name=Name(str(vmid)), link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    vmid = vm['vmid']
                    name = vm.get('name', f"VM-{vmid}")
                    peer = Peer(
                        service_name=Name(name),
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
                    links.append(Link(name=Name(str(vmid)), link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
        except Exception as e:
            logger.error(f"Failed to discover Proxmox links: {e}")
        return links

    def discover_services(self):
        services = ArrayOf(Service)()
        try:
            link_names = ArrayOf(Name)([link.name for link in self.my_links])
            proxmox_service = Service(
                name=Name("proxmox"),
                type=ServiceType("vm"),
                links=link_names,
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
        except Exception as e:
            logger.error(f"Failed to create Proxmox service: {e}")
        return services
