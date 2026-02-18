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
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.types.data.l4_protocol import L4Protocol
from otupy.types.data.hostname import Hostname
from otupy.types.base.array_of import ArrayOf
from otupy import actuator_implementation

logger = logging.getLogger(__name__)


@actuator_implementation("ctxd-proxmox")
class CTXDActuatorProxmox(CTXDActuator):

    def __init__(self, auth, **kwargs):
        """
        auth must contain:
            proxmox_host
            username
            password
            verify_ssl
        """

        kwargs['auth'] = auth
        super().__init__(**kwargs)

        self.proxmox_host = auth['proxmox_host']
        self.username = auth['username']
        self.password = auth['password']
        self.verify_ssl = auth.get('verify_ssl', False)

        self.proxmox = None
        self._connect()

    def is_available(self):
        return True

    def _connect(self):
        try:
            self.proxmox = ProxmoxAPI(
                self.proxmox_host,
                user=self.username,
                password=self.password,
                verify_ssl=self.verify_ssl
            )
            logger.info("Connected to Proxmox host %s", self.proxmox_host)
        except Exception as e:
            logger.error("Connection to Proxmox failed: %s", e)
            raise


    def discover_services(self):
        """
        Populate self.services with:
            - Root Proxmox service
            - VM services
            - Container services
        """

        asset_id = self.specifiers.get('asset_id', 'proxmox')

        cloud = Cloud(
            description="Proxmox Virtual Environment",
            id=self.proxmox_host,
            name="Proxmox"
        )

        # Root service
        self.services.append(Service(
            name=Name(asset_id),
            type=ServiceType(cloud),
            subservices=ArrayOf(Name)(),
            owner=self.owner,
            release=None
        ))

        try:
            nodes = self.proxmox.nodes.get()

            for node in nodes:
                node_name = node['node']

                # LXC Containers
                for ct in self.proxmox.nodes(node_name).lxc.get():
                    name = ct.get('name')
                    if not name:
                        continue

                    self.services.append(Service(
                        name=Name(f"{name}-{ct['vmid']}"),
                        type=ServiceType(cloud),
                        subservices=ArrayOf(Name)(),
                        owner=self.owner,
                        release=None
                    ))

                # QEMU VMs
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    name = vm.get('name')
                    if not name:
                        continue

                    self.services.append(Service(
                        name=Name(f"{name}-{vm['vmid']}"),
                        type=ServiceType(cloud),
                        subservices=ArrayOf(Name)(),
                        owner=self.owner,
                        release=None
                    ))

        except Exception as e:
            logger.error("Service discovery failed: %s", e)


    def discover_links(self):
        """
        Populate self.links with:
            - Root -> VM
            - Root -> Container
        """

        asset_id = self.specifiers.get('asset_id', 'proxmox')

        try:
            nodes = self.proxmox.nodes.get()

            for node in nodes:
                node_name = node['node']

                # Containers
                for ct in self.proxmox.nodes(node_name).lxc.get():
                    name = ct.get('name')
                    if not name:
                        continue

                    peer = Peer(
                        service_name=Name(f"{name}-{ct['vmid']}"),
                        role=PeerRole.controlled,
                        consumer=self.get_consumer(Name(f"{name}-{ct['vmid']}"))
                    )

                    self.links.append(Link(
                        name=Name(asset_id),
                        link_type=LinkType.hosting,
                        peers=ArrayOf(Peer)([peer])
                    ))

                # VMs
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    name = vm.get('name')
                    if not name:
                        continue

                    peer = Peer(
                        service_name=Name(f"{name}-{vm['vmid']}"),
                        role=PeerRole.controlled,
                        consumer=self.get_consumer(Name(f"{name}-{vm['vmid']}"))
                    )

                    self.links.append(Link(
                        name=Name(asset_id),
                        link_type=LinkType.hosting,
                        peers=ArrayOf(Peer)([peer])
                    ))

        except Exception as e:
            logger.error("Link discovery failed: %s", e)
