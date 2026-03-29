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
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.host_type import HostType
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
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

        self._discover_Azure_cloud()
    

    def _discover_Azure_cloud(self):
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


    def discover_links(self):
        """ Discover links between AKS resources """

        asset_id = None
        if self.specifiers and 'asset_id' in self.specifiers:
            asset_id = self.specifiers['asset_id']
        else:
            asset_id = "azure-aks"

        links = ArrayOf(Link)()

        # Cloud -> Node
        for node in self.nodes:
            peer_node = Peer(
                service_name=Name(node),
                role=PeerRole.controlled,
                consumer=None
            )
            links.append(Link(
                name=Name(asset_id),
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer_node])
            ))

        # Node -> Namespace
        for pod in self.pods:
            peer_ns = Peer(
                service_name=Name(pod["namespace"]),
                role=PeerRole.control,
                consumer=None
            )
            links.append(Link(
                name=Name(pod["node"]),
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer_ns])
            ))

        # Namespace -> Pod
        for pod in self.pods:
            peer_pod = Peer(
                service_name=Name(pod["name"]),
                role=PeerRole.guest,
                consumer=None
            )
            links.append(Link(
                name=Name(pod["namespace"]),
                link_type=LinkType.control,
                peers=ArrayOf(Peer)([peer_pod])
            ))

        self.links = links

