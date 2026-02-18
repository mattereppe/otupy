""" Azure Actuator Manager for CTXD

    This module implements a CTXD actuator for Azure Kubernetes Service (AKS).
    It discovers AKS resources (nodes, namespaces, pods) and maps them into 
    `Service` and `Link` objects compatible with the CTXD profile.
"""

import subprocess
import logging

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.server import Server
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.service_type import ServiceType
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


def aks(resource_group, cluster_name, cmd: str) -> str:
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
        resource_group = auth['resource_group'] 
        cluster_name = auth['cluster_name'] 
        self.nodes = set()
        self.namespaces = set()
        self.pods = []

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

    def is_available(self):
        """ Return True if the actuator is available """
        return True

    def discover_services(self):
        """ Discover all services in the AKS cluster

            Populates `self.services` with `Service` instances for Cloud, Nodes, Namespaces, and Pods.
        """
        # Root cloud service
        cloud = Cloud(description="Azure Kubernetes Service", id=None, name=self.asset_id)
        self.services.append(Service(
            name=Name(self.asset_id),
            type=ServiceType(cloud),
            subservices=ArrayOf(Name)(),  # Will fill links later
            owner=self.owner,
            release=None
        ))

        # Nodes as services
        for node in self.nodes:
            self.services.append(Service(
                name=Name(node),
                type=ServiceType(cloud),  # treated as cloud-related service
                subservices=ArrayOf(Name)(),
                owner=self.owner,
                release=None
            ))

        # Namespaces as services
        for ns in self.namespaces:
            self.services.append(Service(
                name=Name(ns),
                type=ServiceType(cloud),
                subservices=ArrayOf(Name)(),
                owner=self.owner,
                release=None
            ))

        # Pods as services
        for pod in self.pods:
            self.services.append(Service(
                name=Name(pod["name"]),
                type=ServiceType(cloud),
                subservices=ArrayOf(Name)(),
                owner=self.owner,
                release=None
            ))

    def discover_links(self):
        """ Discover links between AKS resources

            Populates `self.links` with `Link` instances mapping Cloud -> Node -> Namespace -> Pod.
        """
        links = ArrayOf(Link)()

        # Map nodes -> namespaces
        namespace_to_node = {pod["namespace"]: pod["node"] for pod in self.pods}

        # Node -> Namespace
        for ns, node in namespace_to_node.items():
            peer_ns = Peer(
                service_name=Name(ns),
                role=PeerRole.control,
                consumer=self.get_consumer(Name(ns))
            )
            links.append(Link(
                name=Name(node),
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer_ns])
            ))

        # Namespace -> Pod
        for pod in self.pods:
            ns = pod["namespace"]
            pod_name = pod["name"]
            peer_pod = Peer(
                service_name=Name(pod_name),
                role=PeerRole.guest,
                consumer=self.get_consumer(Name(pod_name))
            )
            links.append(Link(
                name=Name(ns),
                link_type=LinkType.control,
                peers=ArrayOf(Peer)([peer_pod])
            ))

        # Cloud -> Node
        for node in self.nodes:
            peer_node = Peer(
                service_name=Name(node),
                role=PeerRole.controlled,
                consumer=self.get_consumer(Name(node))
            )
            links.append(Link(
                name=Name(self.asset_id),
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer_node])
            ))

        self.links = links
