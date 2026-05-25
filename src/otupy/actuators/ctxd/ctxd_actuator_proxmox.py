"""
Proxmox Actuator Manager
"""

import functools
import logging

from proxmoxer import ProxmoxAPI

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.actuators.ctxd.metrics import MetricsCollector
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.host_type import HostType
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.network_interface import IPInfo, NetworkInterface
from otupy.profiles.ctxd.data.network_node import NetworkNode
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.service import SId, Service
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.network_type import NetworkType
from otupy.profiles.ctxd.data.ethernet_network import EthernetNetwork
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.base.array_of import ArrayOf
from otupy import actuator_implementation

logger = logging.getLogger(__name__)


def measure_latency(func):
    """Class-method decorator that times a Proxmox API helper.

    Unlike the previous version (which appended CSV rows to
    ``latency_log.txt``), this decorator routes the measurement through
    the shared :class:`MetricsCollector` attached to the actuator
    instance as ``self._metrics``. The collector is configured from
    the actuator YAML (the ``metrics:`` block); when it is disabled,
    the decorator is effectively a pass-through and the call is not
    timed.

    The wrapped function's name is used as the call label, matching the
    convention used by the Azure actuator (``get_nodes``,
    ``get_pods:<ns>``, etc.) so that a single parser can post-process
    output from both actuators.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        metrics = getattr(self, "_metrics", None)
        if metrics is None or not getattr(metrics, "enabled", False):
            return func(self, *args, **kwargs)

        import time
        label = func.__name__
        t_start = time.perf_counter()
        try:
            result = func(self, *args, **kwargs)
            elapsed = time.perf_counter() - t_start
            # Best-effort payload size; for proxmoxer this is usually a
            # list of dicts whose len() reflects how many items came back.
            try:
                bytes_out = len(result) if hasattr(result, "__len__") else 0
            except Exception:
                bytes_out = 0
            metrics.record(label, elapsed, success=True,
                           bytes_out=bytes_out, cmd=label)
            return result
        except Exception:
            elapsed = time.perf_counter() - t_start
            metrics.record(label, elapsed, success=False,
                           bytes_out=0, cmd=label)
            raise
    return wrapper


@actuator_implementation("ctxd-proxmox")
class CTXDActuatorProxmox(CTXDActuator):

    def __init__(self, auth, metrics=None, **kwargs):
        """Initialize the Proxmox actuator.

        :param auth:    dict with the Proxmox credentials. Required keys:
                        ``proxmox_host``, ``username``, ``password``.
                        Optional: ``verify_ssl`` (default False).
        :param metrics: optional dict controlling per-call timing logs.
                        Forwarded verbatim to
                        :class:`otupy.actuators.ctxd.metrics.MetricsCollector`.
                        See its docstring for the recognized keys
                        (``enabled``, ``file``, ``mode``, ``propagate``).
                        When omitted or ``enabled: false``, no timing
                        file is produced.
        """
        kwargs['auth'] = auth
        super().__init__(**kwargs)

        self.proxmox_host = auth['proxmox_host']
        self.username = auth['username']
        self.password = auth['password']
        self.verify_ssl = auth.get('verify_ssl', False)

        self.active_only = (
            kwargs['config']['active_only']
            if 'config' in kwargs and 'active_only' in kwargs['config']
            else False
        )
        self.cloud_name = (
            kwargs['config']['cloud_name']
            if 'config' in kwargs and 'cloud_name' in kwargs['config']
            else 'proxmox'
        )

        self.nodes = []
        self._node_bridges: dict[str, list] = {}
        self._vm_node_map: dict[int, str] = {}

        # Cached Service objects for the cloud and each node,
        # so link-discovery methods can reference them directly
        # without re-querying self.services.
        self._cloud_service: Service | None = None
        self._node_services: dict[str, Service] = {}   # node_name -> Service

        # Per-actuator metrics collector. Shared format with the Azure
        # actuator, so a single parser can post-process both.
        self._metrics = MetricsCollector("ctxd-proxmox", metrics)

        self.proxmox_conn = None
        self._connect()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self):
        try:
            self.proxmox_conn = ProxmoxAPI(
                self.proxmox_host,
                user=self.username,
                password=self.password,
                verify_ssl=self.verify_ssl,
            )
            logger.info("Connected to Proxmox host %s", self.proxmox_host)
        except Exception as e:
            logger.error("Connection to Proxmox failed: %s", e)
            raise

    # ------------------------------------------------------------------
    # Top-level entry points
    # ------------------------------------------------------------------

    def discover_context(self):
        self._metrics.start_run()
        try:
            self.nodes = self.get_cluster_nodes()
            resources = self.proxmox_conn.cluster.resources.get(type="vm")
            self._vm_node_map = {r['vmid']: r['node'] for r in resources}
            self.discover_services()
            self.discover_links()
        finally:
            self._metrics.end_run()

    def discover_services(self):
        self._discover_proxmox_nodes()
        self._discover_proxmox_vms()
        self._discover_proxmox_lxc()
        self._discover_networks()

    def discover_links(self):
        self._discover_nodes_link_cloud()    # execenv -> cloud
        self._discover_vms_link_nodes()      # host    -> execenv
        self._discover_vms_link_networks()   # host    -> network
        self._discover_networks_link_nodes() # network -> execenv

    # ------------------------------------------------------------------
    # Service discovery
    # ------------------------------------------------------------------

    def _discover_proxmox_nodes(self):
        """
        Register each physical Proxmox node as an ExecutionEnvironment service,
        then create the root Cloud service with all nodes as subservices.

        The Cloud service is cached in self._cloud_service and each node
        service in self._node_services so that link-discovery methods can
        reference them without scanning self.services again.
        """
        node_sids = ArrayOf(SId)()

        for h in self.nodes:
            node_ee = ExecutionEnvironment(
                name=Hostname(h['node']),
                id=h['node'],
                description="Proxmox physical node",
                type=ExecutionEnvironmentType(OS()),
            )
            node_sid = SId.create_from_service_type(node_ee)
            node_sids.append(node_sid)

            node_svc = Service(
                name=Name(str(h['node'])),
                sid=node_sid,
                type=ServiceType(node_ee),
                subservices=ArrayOf(SId)(),
                owner=self.owner,
                release=None,
            )
            self.services.append(node_svc)
            self._node_services[h['node']] = node_svc
            logger.debug("Found Proxmox node: %s", h['node'])

        proxmox_cloud = Cloud(
            description='Proxmox VE cluster',
            id=None,
            name=self.cloud_name,
            type='proxmox',
        )
        cloud_svc = Service(
            name=Name(self.cloud_name),
            sid=SId.create_from_service_type(proxmox_cloud),
            type=ServiceType(proxmox_cloud),
            subservices=node_sids,
            owner=self.owner,
            release=None,
        )
        self.services.append(cloud_svc)
        self._cloud_service = cloud_svc

    def _discover_proxmox_vms(self):
        """
        Discover QEMU VMs. Each VM becomes a Host service with a NetworkNode
        subservice for its interfaces.
        """
        for node in self.nodes:
            for vm in self.get_all_vms(node):
                if self.active_only and vm.get('status') != 'running':
                    continue

                config = self.proxmox_conn.nodes(node['node']).qemu(vm['vmid']).config.get()
                ifaces = ArrayOf(NetworkInterface)()

                try:
                    vm_details = self.proxmox_conn.nodes(node['node']).qemu(
                        vm['vmid']
                    ).agent("network-get-interfaces").get()

                    for iface in vm_details.get("result", []):
                        ips = ArrayOf(IPInfo)()
                        for ip_info in iface.get("ip-addresses", []):
                            try:
                                ips.append(IPInfo(
                                    ip=ip_info["ip-address"],
                                    prefix=ip_info["prefix"],
                                    gw=None,
                                ))
                            except Exception as e:
                                logger.error("Unable to add IP for VM %s: %s", vm['vmid'], e)
                        ifaces.append(NetworkInterface(
                            description=vm.get('name', str(vm['vmid'])),
                            id=f"{vm['vmid']}.{iface['name']}",
                            iface=iface["name"],
                            ips=ips,
                        ))
                except Exception as e:
                    logger.warning("Guest agent unavailable for VM %s: %s", vm['vmid'], e)

                netnode = NetworkNode(
                    name=vm.get('name', str(vm['vmid'])),
                    description=f"Proxmox network interfaces for QEMU VM {vm['vmid']}",
                    ifaces=ifaces,
                )
                server = Host(
                    name=vm.get('name', str(vm['vmid'])),
                    id=vm['vmid'],
                    description=vm.get('name', ''),
                    type=HostType(VM(
                        hypervisor='QEMU',
                        hypervisor_type="native",
                        image=config.get('ostype'),
                    )),
                )

                name = Name(server.name)
                netnode_name = Name(server.name + ".interfaces")
                netnode_sid = SId.create_from_service_type(netnode)

                vm_service = Service(
                    name=name,
                    sid=SId.create_from_service_type(server),
                    type=ServiceType(server),
                    subservices=ArrayOf(SId)([netnode_sid]),
                    owner=self.owner,
                    release=None,
                )
                self.services.append(vm_service)
                self.services.append(Service(
                    name=netnode_name,
                    sid=netnode_sid,
                    type=ServiceType(netnode),
                    subservices=ArrayOf(SId)(),
                    owner=str(name),
                    release=None,
                ))

    def _discover_proxmox_lxc(self):
        """
        Discover LXC containers. Same structure as QEMU VMs: Host + NetworkNode.
        """
        for node in self.nodes:
            for ct in self.get_all_containers(node):
                if self.active_only and ct.get('status') != 'running':
                    continue

                vmid = ct['vmid']
                config = self.proxmox_conn.nodes(node['node']).lxc(vmid).config.get()
                ifaces = ArrayOf(NetworkInterface)()

                for key, value in config.items():
                    if key.startswith('net') and isinstance(value, str):
                        ifaces.append(NetworkInterface(
                            description=f"LXC {vmid} {key}",
                            id=f"{vmid}.{key}",
                            iface=key,
                            ips=ArrayOf(IPInfo)(),
                        ))

                netnode = NetworkNode(
                    name=ct.get('name', str(vmid)),
                    description=f"Proxmox network interfaces for LXC container {vmid}",
                    ifaces=ifaces,
                )
                server = Host(
                    name=ct.get('name', str(vmid)),
                    id=vmid,
                    description=f"LXC Container: {config.get('hostname', ct.get('name', str(vmid)))}",
                    type=HostType(VM(
                        hypervisor='LXC',
                        hypervisor_type="native",
                        image=config.get('ostype', 'linux'),
                    )),
                )

                name = Name(server.name)
                netnode_name = Name(server.name + ".interfaces")
                netnode_sid = SId.create_from_service_type(netnode)

                ct_service = Service(
                    name=name,
                    sid=SId.create_from_service_type(server),
                    type=ServiceType(server),
                    subservices=ArrayOf(SId)([netnode_sid]),
                    owner=self.owner,
                    release=None,
                )
                self.services.append(ct_service)
                self.services.append(Service(
                    name=netnode_name,
                    sid=netnode_sid,
                    type=ServiceType(netnode),
                    subservices=ArrayOf(SId)(),
                    owner=str(name),
                    release=None,
                ))

    def _discover_networks(self):
        """
        Discover Linux bridges per node and register them as Network services.
        """
        self._node_bridges = {}

        for node in self.nodes:
            node_name = node['node']
            bridges = self.get_node_bridges(node)
            self._node_bridges[node_name] = bridges

            for bridge in bridges:
                bridge_name = bridge.get('iface', bridge.get('name', ''))
                if not bridge_name:
                    continue

                eth = EthernetNetwork({'nets': ArrayOf(IPNetAddress)()})
                net = Network(
                    name=bridge_name,
                    description=f"Proxmox Linux bridge on node {node_name}",
                    id=bridge.get('id', bridge_name),
                    type=NetworkType(eth),
                )
                self.services.append(Service(
                    name=Name(bridge_name),
                    sid=SId.create_from_service_type(net),
                    type=ServiceType(net),
                    subservices=ArrayOf(SId)(),
                    owner=self.owner,
                    release=None,
                ))
                logger.debug("Found bridge %s on node %s", bridge_name, node_name)

    # ------------------------------------------------------------------
    # Link discovery
    # ------------------------------------------------------------------

    def _discover_nodes_link_cloud(self):
        """
        Add hosting links: physical node -> Proxmox cloud.
        """
        if self._cloud_service is None:
            logger.warning("Cloud service not found; skipping node->cloud links")
            return

        for node_name, node_svc in self._node_services.items():
            peer = Peer(
                service_name=self._cloud_service.name,
                sid=self._cloud_service.sid,
                role=PeerRole.host,
                consumer=None,
            )
            self.links.append(Link(
                name=node_svc.name,
                sid=node_svc.sid,
                description=f"Node {node_name} is part of Proxmox cluster",
                role=PeerRole.guest,
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer]),
            ))

    def _discover_vms_link_nodes(self):
        """
        Add hosting links: VM/container -> physical node that runs it.
        """
        proxmox_vms = self.get_services_by_sid(
            SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM))
        )

        for v in proxmox_vms:
            vmid = v.type.getObj().id
            node_name = self._vm_node_map.get(vmid)
            if node_name is None:
                logger.warning("Cannot find hosting node for VM/CT id=%s", vmid)
                continue

            node_svc = self._node_services.get(node_name)
            if node_svc is None:
                logger.warning("Node service not cached for %s", node_name)
                continue

            peer = Peer(
                service_name=node_svc.name,
                sid=node_svc.sid,
                role=PeerRole.host,
                consumer=self.get_consumer(node_name),
            )
            self.links.append(Link(
                name=v.name,
                sid=v.sid,
                description=f"VM/CT {v.name} hosted on {node_name}",
                role=PeerRole.guest,
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer]),
            ))

    def _discover_vms_link_networks(self):
        """
        Add packet-flow links: VM/container -> bridge network.
        """
        proxmox_vms = self.get_services_by_sid(
            SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM))
        )
        network_services = self.get_services(filter=Network)

        bridge_service_map: dict[str, Service] = {
            svc.type.getObj().name: svc
            for svc in network_services
        }

        for v in proxmox_vms:
            vmid = v.type.getObj().id
            node_name = self._vm_node_map.get(vmid)
            if node_name is None:
                continue

            attached_bridges: set[str] = set()
            try:
                try:
                    config = self.proxmox_conn.nodes(node_name).qemu(vmid).config.get()
                except Exception:
                    config = self.proxmox_conn.nodes(node_name).lxc(vmid).config.get()

                for key, value in config.items():
                    if key.startswith('net') and isinstance(value, str) and 'bridge=' in value:
                        for part in value.split(','):
                            if part.startswith('bridge='):
                                attached_bridges.add(part.split('=', 1)[1].strip())
            except Exception as e:
                logger.error("Could not fetch config for VM/CT %s: %s", vmid, e)
                continue

            for bridge_name in attached_bridges:
                net_svc = bridge_service_map.get(bridge_name)
                if net_svc is None:
                    logger.warning("Bridge %s not discovered (VM %s)", bridge_name, vmid)
                    continue

                self.links.append(Link(
                    name=v.name,
                    sid=v.sid,
                    description=f"VM/CT {v.name} attached to bridge {bridge_name}",
                    role=PeerRole.endpoint,
                    link_type=LinkType.packet_flow,
                    peers=ArrayOf(Peer)([Peer(
                        service_name=net_svc.name,
                        sid=net_svc.sid,
                        role=PeerRole.forwarding,
                        consumer=None,
                    )]),
                ))

    def _discover_networks_link_nodes(self):
        """
        Add hosting links: bridge network -> physical node that owns it.
        Uses the cached _node_services to avoid re-building SIds.
        """
        for node_name, bridges in self._node_bridges.items():
            node_svc = self._node_services.get(node_name)
            if node_svc is None:
                continue

            controller_peer = Peer(
                service_name=node_svc.name,
                sid=node_svc.sid,
                role=PeerRole.host,
                consumer=self.get_consumer(node_svc.name),
            )

            for bridge in bridges:
                bridge_name = bridge.get('iface', bridge.get('name', ''))
                if not bridge_name:
                    continue

                for n in self.get_services(name=Name(bridge_name), filter=Network):
                    self.links.append(Link(
                        name=n.name,
                        sid=n.sid,
                        description=f"Bridge {bridge_name} hosted on node {node_name}",
                        link_type=LinkType.hosting,
                        role=PeerRole.guest,
                        peers=ArrayOf(Peer)([controller_peer]),
                    ))

    # ------------------------------------------------------------------
    # Proxmox API helpers
    # ------------------------------------------------------------------

    @measure_latency
    def get_cluster_nodes(self):
        return self.proxmox_conn.nodes.get()

    @measure_latency
    def get_all_vms(self, node):
        return self.proxmox_conn.nodes(node['node']).qemu.get()

    @measure_latency
    def get_all_containers(self, node):
        return self.proxmox_conn.nodes(node['node']).lxc.get()

    @measure_latency
    def get_node_networks(self, node):
        return self.proxmox_conn.nodes(node['node']).network.get()

    @measure_latency
    def get_node_bridges(self, node):
        return self.proxmox_conn.nodes(node['node']).network.get(type="bridge")

    @measure_latency
    def get_node_storage(self, node):
        return self.proxmox_conn.nodes(node['node']).storage.get()

    @measure_latency
    def get_interfaces(self, node):
        return self.proxmox_conn.nodes(node['node']).network.get()

    @measure_latency
    def get_interfaces_vm(self, node, vm):
        return self.proxmox_conn.nodes(node['node']).qemu(
            vm['vmid']
        ).agent("network-get-interfaces").get()