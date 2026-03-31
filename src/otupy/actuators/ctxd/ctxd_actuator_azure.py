""" Azure Actuator Manager for CTXD

    This module implements a CTXD actuator for Azure Kubernetes Service (AKS).
    It discovers AKS resources (nodes, namespaces, pods) and maps them into 
    `Service` and `Link` objects compatible with the CTXD profile.
"""

import json
import subprocess
import logging
from types import SimpleNamespace

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.host_type import HostType
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.network_interface import IPAddress, IPInfo, NetworkInterface
from otupy.profiles.ctxd.data.network_node import NetworkNode
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.port import Port
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.service import SId, Service
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol
from otupy.core.transfer import Transfer
from otupy import ArrayOf, actuator_implementation

logger = logging.getLogger(__name__)


def run(cmd):
    """ Run a subprocess command and return success, stdout, stderr """
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
        return p.returncode == 0, out.strip(), err.strip()
    except Exception as e:
        logger.warning("Command execution failed: %s", e)
        return False, "", str(e)


def aks_cmd(resource_group, cluster_name, cmd: str) -> str:
    """ Execute a command on the AKS cluster using Azure CLI """
    full_cmd = [
        "az", "aks", "command", "invoke",
        "--resource-group", resource_group,
        "--name", cluster_name,
        "--command", cmd
    ]
    success, out, err = run(full_cmd)
    if not success:
        logger.warning("AKS command failed: %s", err)
        return ""
    return out


@actuator_implementation("ctxd-azure")
class CTXDActuatorAzure(CTXDActuator):
    """ Azure Actuator Manager

        Extends the base `CTXDActuator` to retrieve services and links for an AKS cluster.
        Implements `discover_services()` and `discover_links()` required by the base class.
    """
    
    def __init__(self,  auth,**kwargs):
        """ Initialize the actuator

            :param tenant_id: Azure tenant ID
            :param client_id: Azure client ID
            :param client_secret: Azure client secret
            :param resource_group: Azure resource group
            :param cluster_name: AKS cluster name
        """
        
        kwargs['auth']=auth
        
        super().__init__(**kwargs)
        
        tenant_id = auth['tenant_id'] 
        client_id = auth['client_id'] 
        client_secret = auth['client_secret'] 
        self.resource_group = auth['resource_group'] 
        self.cluster_name = auth['cluster_name'] 
        self.nodes = set()
        self.namespaces = set()
        self.pods = []

        self._aks_nodes = {} 
        self._aks_pods = {}
        """
        # Retrieve pods from AKS
        pods_raw = aks(
            resource_group,
            cluster_name,
            "kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.nodeName}|{.metadata.namespace}|{.metadata.name}\n{end}'"
        )

        for line in pods_raw.splitlines():
            parts = line.split("|")
            if len(parts) != 3:
                continue
            node, namespace, pod_name = parts
            self.nodes.add(node)
            self.namespaces.add(namespace)
            self.pods.append({"name": pod_name, "namespace": namespace, "node": node})

        self.nodes = list(self.nodes)
        self.namespaces = list(self.namespaces)
        
        """
        

    def is_available(self):
        """ Return True if the actuator is available """
        return True

    def discover_context(self):
        """ Discover the context of the AKS cluster """

        self.discover_services()
        self.discover_links()


    def discover_services(self):

        self._discover_AKS_cloud()
        self._discover_AKS_pods()
    

    def _discover_AKS_cloud(self):
        # The root service: AKS cluster
        # --------------------------------------------------
        # AKS is considered IaaS
        aks = Cloud(description='Azure cloud', id=None, name="AKS", type='AKS')
        aks_subservices = ArrayOf(SId)()

        
        raw_output = aks_cmd(
            self.resource_group, 
            self.cluster_name, 
            "kubectl get nodes -o json"
        )
        if raw_output:
        

            try:
                # 2. Parse the wrapper and the nested kubectl JSON
                wrapper = json.loads(raw_output[raw_output.find('{'):])
                
                
            
                node_items = wrapper.get("items", [])
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to parse AKS JSON: %s", e)
                return

            for n_data in node_items:

                n = json.loads(json.dumps(n_data), object_hook=lambda d: SimpleNamespace(**d))

                
                
                # A Kubernetes node is an execution environment and hosts a kubelet
                node = ExecutionEnvironment(name=n.metadata.name, id=n.metadata.uid, version=n.status.nodeInfo.kernelVersion,
						description="AKS node "+n.status.nodeInfo.containerRuntimeVersion,
                  type= ExecutionEnvironmentType( OS(family=n.status.nodeInfo.operatingSystem, arch=n.status.nodeInfo.architecture,
							version=n.status.nodeInfo.kernelVersion)) )
                self._aks_nodes[n.metadata.name]=SId.create_from_service_type(node)
                logger.debug("Found node: %s", str(node))

                kubelet = Application(
                    name="kubelet", 
                    description="AKS worker node",
                    version=n.status.nodeInfo.kubeletVersion, 
                    owner=self.owner, 
                    app_type="kubelet"
                )

                aks_subservices.append(SId.create_from_service_type(kubelet, domain=n.metadata.name))
            

            self.services.append(Service(name=Name(aks.name),
            sid=SId.create_from_service_type(aks),
            type=ServiceType(aks), 
            subservices=aks_subservices, owner=self.owner, release=None))

    def _discover_AKS_pods(self):
        """ 
        Discovers pods using 'az aks command invoke' and maps them 
        to nodes, containers, and network interfaces.
        """
        self._aks_pods = {}


        ns_output = aks_cmd(self.resource_group, self.cluster_name, "kubectl get ns -o jsonpath='{.items[*].metadata.name}'")
        header_end_marker = "exitcode=0\n"
        start_index = ns_output.find(header_end_marker)
        if start_index != -1:
            ns_output = ns_output[(start_index + len(header_end_marker) ):].strip()
        else:
            logger.warning("Header end marker not found in namespaces output. Using full output.")
            return
        namespaces = ns_output.split()

        for ns in namespaces:
            # 2. Fetch pods one namespace at a time
            raw_output = aks_cmd(
                self.resource_group, 
                self.cluster_name, 
                f"kubectl get pods -n {ns} -o json"
            )
        
            # Using -A for all namespaces and -o json for parsing
            """
            raw_output = aks_cmd(
                self.resource_group, 
                self.cluster_name, 
                "kubectl get pods -A -o json"
            )
            """
            

            if not raw_output:
                logger.error("No output received from AKS command invoke")
                return

            try:
                # 2. Parse the JSON. 
                # Note: 'az aks command invoke' returns a wrapper; the actual kubectl output 
                # is usually in the 'logs' or 'content' field, but if your wrapper 
                # already extracts the JSON string, we parse it directly:
                data = json.loads(raw_output[raw_output.find('{'):])
                pods = data.get("items", [])
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to parse Pod JSON: %s", e)
                return

            
            def _get_container_status_from_json(status_entry):
                state_dict = status_entry.get('state', {})
                if 'running' in state_dict: return 'running'
                if 'waiting' in state_dict: return 'waiting'
                if 'terminated' in state_dict: return 'terminated'
                return 'unknown'

            for pod in pods:
                metadata = pod.get('metadata', {})
                spec = pod.get('spec', {})
                status = pod.get('status', {})
                namespace = metadata.get('namespace')
                pod_name = metadata.get('name')
                pod_uid = metadata.get('uid')
                logger.info(f"Processing pod: {pod_name} in namespace: {namespace}")
                pod_subservices_list = ArrayOf(SId)()

                # --- 3. Network Discovery (Multus / CNI) ---
                port_list = ArrayOf(NetworkInterface)()
                annotations = metadata.get('annotations', {})
                if annotations and 'k8s.v1.cni.cncf.io/network-status' in annotations:
                    try:
                        network_data = json.loads(annotations['k8s.v1.cni.cncf.io/network-status'])
                        for p in network_data:
                            ips = [IPInfo(ip=IPAddress(ip)) for ip in p.get('ips', [])]
                            port_list.append(Port(id=p.get('name'), iface=p.get('iface'), ips=ips))
                    except: pass

                # Register Network Node
                node_type = NetworkNode(description="Pod network ports", id=pod_uid, name=pod_name, ifaces=port_list)
                nodesid = SId.create_from_service_type(node_type, namespace=namespace)
                self.services.append(Service(name=Name(f"{pod_name}.{namespace}.ports"), 
                                            sid=nodesid, type=ServiceType(node_type)))
                pod_subservices_list.append(nodesid)

                # --- 4. Container Discovery ---
                # Combine init and standard containers
                all_statuses = status.get('containerStatuses', []) + status.get('initContainerStatuses', [])
                
                pod_dns_name = Name(f"{pod_name}.{namespace}.pod")
                
                for cs in all_statuses:
                    c_name = cs.get('name')
                    state = _get_container_status_from_json(cs)
                    
                    # Create Execution Environment
                    exe_env = ExecutionEnvironment(
                        name=f"{c_name}.{pod_name}", 
                        id=cs.get('containerID'),
                        type=ExecutionEnvironmentType(Container(namespace=namespace, image=cs.get('image'), status=state))
                    )
                    
                    c_dns_name = Name(Hostname(f"{c_name}.{namespace}.{pod_name}.container"))
                    c_sid = SId.create_from_service_type(exe_env,namespace=namespace)
                    
                    self.services.append(Service(name=c_dns_name, sid=c_sid, type=ServiceType(exe_env)))
                    pod_subservices_list.append(c_sid)
                    
                
                pod_host_type = Host(description="Kubernetes pod", id=pod_uid, name=pod_name, 
                                    type=HostType(Pod(namespace=namespace)))
                pod_sid = SId.create_from_service_type(pod_host_type,namespace=namespace)
                



                if spec.get('nodeName') is not None and spec.get('nodeName') !="":
                    
                    if spec.get('nodeName')not in self._aks_nodes:
					
                     
                        self._aks_nodes[spec.get('nodeName')] =SId(type=ServiceType.get_type_name(ExecutionEnvironment), 
                        subtype=ExecutionEnvironmentType.get_type_name(OS), name=spec.get('nodeName'))
                    self._aks_pods[str(pod_sid)] = self._aks_nodes[spec.get('nodeName')]
                else:
                    self._aks_pods[str(pod_sid)]=None
                        
                self.services.append(Service(
                    name=pod_dns_name, 
                    sid=pod_sid,
                    type=ServiceType(pod_host_type),
                    subservices=pod_subservices_list,
                    release=metadata.get('resourceVersion')
                ))


    def discover_links(self):
        
        self._discover_aks_links_nodes()
        self._discover_aks_links_pods()

    def _discover_aks_links_nodes(self):
        """ Discover AKS links to nodes

        """

        cloud_services = self.get_services(filter=Cloud)

        for cloud in cloud_services:
            for sub in cloud.subservices:
                if sub.type == ServiceType.get_type_name(Application):
                    node = self._aks_nodes[sub.domain]
                    peer = Peer(service_name=node.name, sid=node, role=PeerRole.host, consumer=self.get_consumer(sid=node))
                    self.links.append(Link(name=sub.name, sid=sub, description=sub.name + " hosted on " + str(node),
                        role=PeerRole.guest, link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))
                    

    def _discover_aks_links_pods(self):
        """ 
        Discover AKS links to pods

        """

        cloud_services = self.get_services(filter=Cloud)
        
        cloud_pods=self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(Pod)))
        for cloud in cloud_services:
            for sub in cloud.subservices:
                if sub.type == ServiceType.get_type_name(Application):
                    peer = Peer(service_name=sub.name, sid=sub, role=PeerRole.controlled,consumer=self.get_consumer(sid=sub))
                peer.role=PeerRole.control
                for pod in cloud_pods:
                    if self._aks_pods[str(pod.sid)].name == sub.domain:
                        self.links.append( Link(name=pod.name, sid=pod.sid, 
                                                description="Kubelet controls pod "+str(pod.name),
                                                link_type=LinkType.controlling, role=PeerRole.controlled,
                                                peers=ArrayOf(Peer)([peer])))