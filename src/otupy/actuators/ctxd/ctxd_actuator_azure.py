import subprocess
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
from otupy.profiles.ctxd.data.transfer import Transfer
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy import ArrayOf

def run(cmd):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
        return p.returncode == 0, out.strip(), err.strip()
    except Exception as e:
        return False, "", str(e)

def aks(resource_group, cluster_name, cmd: str) -> str:
    full_cmd = [
        "az", "aks", "command", "invoke",
        "--resource-group", resource_group,
        "--name", cluster_name,
        "--command", cmd
    ]
    success, out, err = run(full_cmd)
    if not success:
        return ""
    return out

class CTXDActuatorAzure(CTXDActuator):
    def is_available(self):
        return True

    def __init__(self, tenant_id, client_id, client_secret, resource_group, cluster_name, **kwargs):
        # CTXD args
        self.domain = kwargs.get("domain")
        self.asset_id = kwargs.get("asset_id")
        self.hostname = kwargs.get("hostname")
        self.ip = kwargs.get("ip")
        self.port = kwargs.get("port")
        self.protocol = kwargs.get("protocol")
        self.endpoint = kwargs.get("endpoint")
        self.transfer = kwargs.get("transfer")
        self.encoding = kwargs.get("encoding")

        # Azure AKS
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.resource_group = resource_group
        self.cluster_name = cluster_name

        # single discovery pass
        pods_raw = aks(
            self.resource_group,
            self.cluster_name,
            "kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.nodeName}|{.metadata.namespace}|{.metadata.name}\n{end}'"
        )

        self.nodes = set()
        self.namespaces = set()
        self.pods = []

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

        # build CTXD
        self.my_links = self.build_links()
        self.my_services = self.build_services()

    def build_links(self):
        links = ArrayOf(Link)()

        # Map namespaces to nodes
        namespace_to_node = {}
        for pod in self.pods:
            node_name = pod.get("node")
            ns_name = pod.get("namespace")
            if node_name and ns_name:
                namespace_to_node[ns_name] = node_name

        # --- Node -> Namespace ---
        for ns_name, node_name in namespace_to_node.items():
            peer_ns = Peer(
                service_name=Name(ns_name),
                role=PeerRole.control,  
                consumer=Consumer(
                    server=Server(Hostname(ns_name)),
                    port=self.port,
                    protocol=L4Protocol(self.protocol),
                    endpoint=self.endpoint,
                    transfer=Transfer(self.transfer),
                    encoding=Encoding(self.encoding)
                )
            )
            links.append(Link(
                name=Name(f"{node_name}"),
                link_type=LinkType.hosting,  # Node hosts Namespace
                peers=ArrayOf(Peer)([peer_ns])
            ))

        # --- Namespace -> Pod ---
        for pod in self.pods:
            pod_name = pod["name"]
            ns_name = pod["namespace"]

            peer_pod = Peer(
                service_name=Name(pod_name),
                # Use dynamic access rights
                role=PeerRole.guest,
                consumer=Consumer(
                    server=Server(Hostname(pod_name)),
                    port=self.port,
                    protocol=L4Protocol(self.protocol),
                    endpoint=self.endpoint,
                    transfer=Transfer(self.transfer),
                    encoding=Encoding(self.encoding)
                )
            )
            links.append(Link(
                name=Name(f"{ns_name}"),
                link_type=LinkType.control,  # Namespace controls Pod
                peers=ArrayOf(Peer)([peer_pod])
            ))

        # --- Cloud -> Node ---
        cloud_name = self.asset_id
        for node in self.nodes:
            peer_node = Peer(
                service_name=Name(node),
                # Node is controlled by Cloud
                role=PeerRole.controlled,
                consumer=Consumer(
                    server=Server(Hostname(node)),
                    port=self.port,
                    protocol=L4Protocol(self.protocol),
                    endpoint=self.endpoint,
                    transfer=Transfer(self.transfer),
                    encoding=Encoding(self.encoding)
                )
            )
            links.append(Link(
                name=Name(f"{cloud_name}"),
                link_type=LinkType.hosting,
                peers=ArrayOf(Peer)([peer_node])
            ))

        return links


    def build_services(self):
        cloud = Cloud(description="Azure Kubernetes Service", id=None, name=self.asset_id)
        service = Service(
            name=Name(self.asset_id),
            type=ServiceType(cloud),
            links=ArrayOf(Name)([link.name.obj for link in self.my_links]),
            actuator=Consumer(
                server=Server(Hostname(self.hostname)),
                port=self.port,
                protocol=L4Protocol(self.protocol),
                endpoint=self.endpoint,
                transfer=Transfer(self.transfer),
                encoding=Encoding(self.encoding)
            )
        )
        return ArrayOf(Service)([service])
