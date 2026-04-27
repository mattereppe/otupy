import logging
from proxmoxer import ProxmoxAPI

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.host_type import HostType
from otupy.profiles.ctxd.data.network_interface import IPInfo, NetworkInterface
from otupy.profiles.ctxd.data.network_node import NetworkNode
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.service import SId, Service
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.vm import VM
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
        self.networks=None
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

    def discover_context(self):

        self.nodes = self.get_cluster_nodes()
        self.discover_services()
        self.discover_links()
        
    
    def discover_links(self):
        """
        VMs (qemu) and physical servers (nodes)
        
        """

        self._discover_vms_link_nodes()
    





    def discover_services(self):
        """ Discover all services related to Proxmox

        KVM/qemu, containers, storage and networks
            
        """
        self._discover_proxmox_servers()
        self._discover_proxmox_vm()
        self._discover_proxmox_lxc()
        self._discover_networks()

    def _discover_proxmox_servers(self):

         for h in self.nodes:
            node = ExecutionEnvironment(name=Hostname(h['node']), id=h['node'],
					 description="Proxmox physical server", type=ExecutionEnvironmentType(OS()) )
            
            logger.debug("Found node of proxmox: %s", str(node))
            
            self.services.append(Service(name=Name(str(h['node'])), sid=SId.create_from_service_type(node),
						type=ServiceType(node), 
						subservices=None, owner=self.owner, release=None))    

    def _discover_proxmox_vm(self):

        for node in self.nodes:
            vms = self.get_all_vms(node)
            for vm in vms:
                
                config = self.proxmox.nodes(node['node']).qemu(vm['vmid']).config.get()
                ifaces = ArrayOf(NetworkInterface)()

                try:
                    # The agent must be installed to retrieve IP Informatio
                    #vm_details = config_response['result']
                    vm_details = self.proxmox.nodes(node['node']).qemu(vm['vmid']).agent("network-get-interfaces").get()
                    
                    for iface in vm_details["result"]:
                        ips = ArrayOf(IPInfo)()
                        for ip_info in iface["ip-addresses"]:
                            ip = ip_info["ip-address"]
                            prefix = ip_info["prefix"]
                            gw = None
                            ips.append(IPInfo(ip=ip, prefix=prefix, gw=gw))
                        ifaces.append(NetworkInterface(description=vm['name'], id=f"{vm['vmid']}.{iface['name']}", iface=iface["name"], ips=ips))


                except Exception as e:
                    logger.error("Unable to add ip address: ", e)


                netnode = NetworkNode(name=vm['name'], description=f"Proxmox interfaces for id: {vm['vmid']}", ifaces=ifaces)
                server = Host(name= vm['name'],
                        id= vm['vmid'], 
                        description=vm['name'],
                        type=HostType(VM(hypervisor='QEMU',hypervisor_type="native",image=config.get('ostype'))))
                logger.debug("Found server: %s", str(server))

                name=Name(server.name)
                netnode_name=Name(server.name+".interfaces")
                netnode_sid=SId.create_from_service_type(netnode)
                
                vm_service = Service(name=name, sid=SId.create_from_service_type(server), 
                                    type=ServiceType(server),  subservices=ArrayOf(SId)(), owner=self.owner, release=None)
                self.services.append(vm_service)
                vm_service.subservices.append(netnode_sid)
                # Add interfaces as subservice
                #self.services.append(Service(name=netnode_name, sid=netnode_sid,
				#		type=ServiceType(netnode),
				#		subservices=ArrayOf(SId)(), owner=str(name), release=None))
                
                #vm_service.subservices.append(netnode_sid)

    def _discover_proxmox_lxc(self):
        """Discover Proxmox LXC containers and map them to Host and Service objects"""
        
        for node in self.nodes:
            
            
            containers = self.get_all_containers(node)
            
            for ct in containers:
                vmid = ct['vmid']
                
                #
                config = self.proxmox.nodes(node['node']).lxc(vmid).config.get()

               
                server = Host(
                    name=ct['name'],
                    id=str(vmid), 
                    description=f"LXC Container: {config.get('hostname', ct['name'])}",
                    type=HostType(
                        
                        VM(
                            hypervisor='LXC',
                            hypervisor_type="native",
                            image=config.get('ostype', 'linux')
                        )
                    )
                )
                
                logger.debug("Found container: %s", str(server))

                name = Name(server.name)
                
                
                lxc_service = Service(
                    name=name, 
                    sid=SId.create_from_service_type(server), 
                    type=ServiceType(server),  
                    subservices=ArrayOf(SId)(), 
                    owner=self.owner, 
                    release=None
                )
                
                self.services.append(lxc_service)


    def _discover_networks(self):
        "Discover network for each node"
        
        for node in self.nodes:
            self.networks = self.get_node_bridges(node)
            logger.debug("Found networks %s",self.networks)
       
    def _discover_vms_link_nodes(self):
        """ 
            Add links between qemu and node that host them


        """	
        
        proxmox_vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

        resources = self.proxmox.cluster.resources.get(type="vm")

        vm_node_map = {r['vmid']: r['node'] for r in resources}

        for v in proxmox_vms:
            vmid = v.type.getObj().id

            node_name = vm_node_map.get(vmid)
            if node_name is None:
                continue
            description = "Proxmox VM " + str(v.name) + " hosted on " + node_name

            consumer = self.get_consumer(node_name)

            peer = Peer(service_name=Name(node_name), 
                        sid=SId.create_from_service_type(ExecutionEnvironment(name=node_name, type=ExecutionEnvironmentType(OS()))),
                        role=PeerRole.host, consumer=consumer)
            self.links.append(Link(name=v.name, sid=v.sid, description=description, role=PeerRole.guest,
                            link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))


    def get_interfaces(self, node):
        """Return List available networks"""
        return self.proxmox.nodes(node['node']).network.get()
    def get_interfaces_vm(self, node,vm):
        """Execute network-get-interfaces."""
        return self.proxmox.nodes(node['node']).qemu(vm['vmid']).agent("network-get-interfaces").get()
    def get_cluster_nodes(self):
        """Returns a list of all physical hosts in the cluster and their health."""
        return self.proxmox.nodes.get()
    def get_all_vms(self, node):
        """Retrieve all Full Virtual Machines on a specific node."""
        return self.proxmox.nodes(node['node']).qemu.get()
    def get_all_containers(self, node):
        """Retrieve all Linux Containers on a specific node."""
        return self.proxmox.nodes(node['node']).lxc.get()
    
    def get_node_networks(self, node):
        """Returns bridges, bonds, and physical NIC configurations."""
        return self.proxmox.nodes(node['node']).network.get()
    def get_node_bridges(self, node):
        """Returns all network bridges visible to this node and their usage."""
        return self.proxmox.nodes(node['node']).network.get(type="bridge")

    def get_node_storage(self, node):
        """Returns all storage pools visible to this node and their usage."""
        return self.proxmox.nodes(node['node']).storage.get()