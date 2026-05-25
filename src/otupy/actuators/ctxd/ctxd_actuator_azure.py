""" Azure Actuator Manager for CTXD

    This module implements a CTXD actuator for Azure Kubernetes Service (AKS).
    It discovers AKS resources (nodes, namespaces, pods, containers, network
    interfaces) and maps them into `Service` and `Link` objects compatible
    with the CTXD profile.

    The actuator does not connect directly to the Kubernetes API server.
    Instead, every `kubectl` query is dispatched through the
    `az aks command invoke` mechanism of the Azure CLI, which relays the
    command to the cluster via the AKS control plane. This makes the
    actuator usable against private clusters and avoids the need to manage
    long-lived Kubernetes service-account tokens.
"""

import json
import logging
import subprocess
import time
from types import SimpleNamespace

from otupy import ArrayOf, actuator_implementation
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.ctxd.data.host import Host
from otupy.profiles.ctxd.data.host_type import HostType
from otupy.profiles.ctxd.data.link import Link
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.network_interface import (
    IPAddress,
    IPInfo,
    NetworkInterface,
)
from otupy.profiles.ctxd.data.network_node import NetworkNode
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.port import Port
from otupy.profiles.ctxd.data.service import SId, Service
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.actuators.ctxd.metrics import MetricsCollector
from otupy.types.data.hostname import Hostname

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd):
    """Run a subprocess command and return (success, stdout, stderr)."""
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = p.communicate()
        return p.returncode == 0, out.strip(), err.strip()
    except Exception as e:
        logger.warning("Command execution failed: %s", e)
        return False, "", str(e)


def _aks_invoke(resource_group, cluster_name, kubectl_cmd, label=None,
                metrics=None):
    """Run a kubectl command on the cluster via `az aks command invoke`.

    Returns the raw textual output (including the Azure wrapper envelope),
    or an empty string if the invocation failed.

    A timing measurement is recorded for every call (when ``metrics`` is
    not ``None`` and enabled): the wall-clock duration of the subprocess,
    the success flag, and the size of the returned payload. The
    measurement is routed through the shared :class:`MetricsCollector`,
    so the format matches what the Proxmox actuator emits.

    :param label:   optional short tag describing the call (e.g.
                    ``"get_nodes"``, ``"get_pods:kube-system"``).
                    Defaults to the kubectl command itself.
    :param metrics: optional :class:`MetricsCollector` instance.
                    When ``None`` or ``not enabled``, no measurement is
                    recorded.
    """
    full_cmd = [
        "az", "aks", "command", "invoke",
        "--resource-group", resource_group,
        "--name", cluster_name,
        "--command", kubectl_cmd,
    ]

    call_label = label or kubectl_cmd
    t_start = time.perf_counter()
    success, out, err = _run(full_cmd)
    elapsed = time.perf_counter() - t_start

    if metrics is not None:
        metrics.record(
            call_label,
            elapsed,
            success=success,
            bytes_out=len(out) if out else 0,
            cmd=kubectl_cmd,
        )

    if not success:
        logger.warning(
            "AKS command invoke failed (label=%s, elapsed=%.3fs): %s",
            call_label, elapsed, err,
        )
        return ""
    return out


def _strip_invoke_envelope_json(raw_output):
    """Parse the JSON payload returned inside an `az aks command invoke` reply.

    The CLI prepends a textual header that ends with `exitcode=<N>` and is
    followed by the actual kubectl output. For JSON payloads, the simplest
    and most robust strategy is to locate the first `{` character and
    `json.loads` from there.

    Returns the parsed dict, or None if no JSON could be extracted.
    """
    if not raw_output:
        return None
    start = raw_output.find("{")
    if start == -1:
        logger.error("No JSON object found in AKS command invoke output.")
        return None
    try:
        return json.loads(raw_output[start:])
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from AKS output: %s", e)
        return None


def _strip_invoke_envelope_text(raw_output):
    """Strip the `az aks command invoke` envelope from a plain-text payload.

    The envelope ends with a line like `exitcode=0\\n`; everything after it
    is the real kubectl output. Returns the stripped payload, or None if
    the marker is missing (which typically indicates a failure).
    """
    if not raw_output:
        return None
    marker = "exitcode=0\n"
    idx = raw_output.find(marker)
    if idx == -1:
        logger.warning(
            "exitcode=0 marker not found in AKS output; payload discarded.")
        return None
    return raw_output[idx + len(marker):].strip()


@actuator_implementation("ctxd-azure")
class CTXDActuatorAzure(CTXDActuator):
    """Azure CTXD actuator.

    Extends the base `CTXDActuator` to discover services and links of an
    AKS cluster. Implements `discover_services()` and `discover_links()` as
    required by the base class.
    """

    def __init__(self, auth, metrics=None, **kwargs):
        """Initialize the actuator.

        :param auth: dict with the Azure credentials and cluster coordinates.
                     Expected keys: ``tenant_id``, ``client_id``,
                     ``client_secret``, ``resource_group``, ``cluster_name``.
        :param metrics: optional dict controlling per-call timing logs.
                        Forwarded verbatim to
                        :class:`otupy.actuators.ctxd.metrics.MetricsCollector`.
                        See its docstring for the recognized keys
                        (``enabled``, ``file``, ``mode``, ``propagate``).
                        When omitted or ``enabled: false``, no timing
                        file is produced and the actuator behaves
                        exactly as before instrumentation was added.
        """
        kwargs["auth"] = auth
        super().__init__(**kwargs)

        # Credentials are kept on the instance for completeness; the actual
        # auth is performed by the Azure CLI session and by the RBAC
        # configuration of the service principal.
        self._tenant_id = auth["tenant_id"]
        self._client_id = auth["client_id"]
        self._client_secret = auth["client_secret"]
        self.resource_group = auth["resource_group"]
        self.cluster_name = auth["cluster_name"]

        # Internal indices populated by the discovery phases.
        # `_aks_nodes`: node name -> SId of the node's ExecutionEnvironment.
        # `_aks_pods` : pod SId (str) -> SId of the node that hosts the pod
        #               (or None if the pod has not been scheduled yet).
        self._aks_nodes = {}
        self._aks_pods = {}

        # Per-actuator metrics collector. Shared format with the Proxmox
        # actuator, so a single parser can post-process both.
        self._metrics = MetricsCollector("ctxd-azure", metrics)

    # ------------------------------------------------------------------ #
    # CTXDActuator interface
    # ------------------------------------------------------------------ #

    def is_available(self):
        """Return True if the actuator is available."""
        return True

    def discover_context(self):
        """Discover the full context of the AKS cluster."""
        self._metrics.start_run()
        try:
            self.discover_services()
            self.discover_links()
        finally:
            self._metrics.end_run()

    def discover_services(self):
        """Discover services in two phases: cluster/nodes, then pods."""
        self._discover_aks_cloud()
        self._discover_aks_pods()

    def discover_links(self):
        """Generate hosting and controlling links between services."""
        self._discover_aks_links_nodes()
        self._discover_aks_links_pods()

    # ------------------------------------------------------------------ #
    # Service discovery
    # ------------------------------------------------------------------ #

    def _discover_aks_cloud(self):
        """Discover the AKS cluster, its worker nodes and their kubelets.

        AKS is classified as a managed container service (PaaS): the cluster
        itself is modeled as a CTXD `Cloud`, each node as an
        `ExecutionEnvironment` of type `OS`, and each node's kubelet as an
        `Application` exposed as a subservice of the cluster.
        """
        aks = Cloud(
            description="Azure cloud",
            id=None,
            name="AKS",
            type="AKS",
        )
        aks_subservices = ArrayOf(SId)()

        raw_output = _aks_invoke(
            self.resource_group,
            self.cluster_name,
            "kubectl get nodes -o json",
            label="get_nodes",
            metrics=self._metrics,
        )
        wrapper = _strip_invoke_envelope_json(raw_output)
        if wrapper is None:
            return

        node_items = wrapper.get("items", [])

        for n_data in node_items:
            # Convert nested dicts to dotted-access objects for readability.
            n = json.loads(
                json.dumps(n_data),
                object_hook=lambda d: SimpleNamespace(**d),
            )

            # Node -> ExecutionEnvironment of type OS.
            node = ExecutionEnvironment(
                name=n.metadata.name,
                id=n.metadata.uid,
                version=n.status.nodeInfo.kernelVersion,
                description="AKS node " + n.status.nodeInfo.containerRuntimeVersion,
                type=ExecutionEnvironmentType(
                    OS(
                        family=n.status.nodeInfo.operatingSystem,
                        arch=n.status.nodeInfo.architecture,
                        version=n.status.nodeInfo.kernelVersion,
                    )
                ),
            )
            self._aks_nodes[n.metadata.name] = SId.create_from_service_type(node)
            logger.debug("Found node: %s", node)

            # Kubelet running on the node -> Application, subservice of AKS.
            kubelet = Application(
                name="kubelet",
                description="AKS worker node",
                version=n.status.nodeInfo.kubeletVersion,
                owner=self.owner,
                app_type="kubelet",
            )
            aks_subservices.append(
                SId.create_from_service_type(kubelet, domain=n.metadata.name)
            )

        self.services.append(
            Service(
                name=Name(aks.name),
                sid=SId.create_from_service_type(aks),
                type=ServiceType(aks),
                subservices=aks_subservices,
                owner=self.owner,
                release=None,
            )
        )

    def _discover_aks_pods(self):
        """Discover pods, their containers and their network interfaces.

        Pods are queried one namespace at a time (rather than with `-A`)
        because on large clusters the cumulative output of `kubectl get
        pods -A -o json` may exceed the maximum response size of
        `az aks command invoke`, leading to truncated payloads.
        """
        self._aks_pods = {}

        # 1. Enumerate namespaces (plain-text payload).
        ns_output = _aks_invoke(
            self.resource_group,
            self.cluster_name,
            "kubectl get ns -o jsonpath='{.items[*].metadata.name}'",
            label="get_namespaces",
            metrics=self._metrics,
        )
        ns_payload = _strip_invoke_envelope_text(ns_output)
        if ns_payload is None:
            logger.error("Could not retrieve namespaces; aborting pod discovery.")
            return
        namespaces = ns_payload.split()

        # 2. For each namespace, list pods and process them individually.
        for ns in namespaces:
            raw_output = _aks_invoke(
                self.resource_group,
                self.cluster_name,
                f"kubectl get pods -n {ns} -o json",
                label=f"get_pods:{ns}",
                metrics=self._metrics,
            )
            data = _strip_invoke_envelope_json(raw_output)
            if data is None:
                logger.warning("Skipping namespace '%s': no parseable output.", ns)
                continue

            for pod in data.get("items", []):
                self._process_pod(pod)

    def _process_pod(self, pod):
        """Translate a single Kubernetes pod into CTXD services."""
        metadata = pod.get("metadata", {})
        spec = pod.get("spec", {})
        status = pod.get("status", {})

        namespace = metadata.get("namespace")
        pod_name = metadata.get("name")
        pod_uid = metadata.get("uid")
        logger.info("Processing pod %s/%s", namespace, pod_name)

        pod_subservices = ArrayOf(SId)()

        # ---- 1. Pod networking from CNI annotation ------------------------
        port_list = ArrayOf(NetworkInterface)()
        annotations = metadata.get("annotations") or {}
        net_status = annotations.get("k8s.v1.cni.cncf.io/network-status")
        if net_status:
            try:
                for p in json.loads(net_status):
                    ips = [IPInfo(ip=IPAddress(ip)) for ip in p.get("ips", [])]
                    port_list.append(
                        Port(
                            id=p.get("name"),
                            iface=p.get("iface"),
                            ips=ips,
                        )
                    )
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(
                    "Failed to parse CNI network-status for %s/%s: %s",
                    namespace, pod_name, e,
                )

        node_type = NetworkNode(
            description="Pod network ports",
            id=pod_uid,
            name=pod_name,
            ifaces=port_list,
        )
        nodesid = SId.create_from_service_type(node_type, namespace=namespace)
        self.services.append(
            Service(
                name=Name(f"{pod_name}.{namespace}.ports"),
                sid=nodesid,
                type=ServiceType(node_type),
            )
        )
        pod_subservices.append(nodesid)

        # ---- 2. Containers (init + standard) ------------------------------
        all_statuses = (
            status.get("containerStatuses", [])
            + status.get("initContainerStatuses", [])
        )

        for cs in all_statuses:
            c_name = cs.get("name")
            state = self._container_state(cs)

            exe_env = ExecutionEnvironment(
                name=f"{c_name}.{pod_name}",
                id=cs.get("containerID"),
                type=ExecutionEnvironmentType(
                    Container(
                        namespace=namespace,
                        image=cs.get("image"),
                        status=state,
                    )
                ),
            )

            c_dns_name = Name(
                Hostname(f"{c_name}.{namespace}.{pod_name}.container")
            )
            c_sid = SId.create_from_service_type(exe_env, namespace=namespace)

            self.services.append(
                Service(name=c_dns_name, sid=c_sid, type=ServiceType(exe_env))
            )
            pod_subservices.append(c_sid)

        # ---- 3. Pod itself -----------------------------------------------
        pod_host_type = Host(
            description="Kubernetes pod",
            id=pod_uid,
            name=pod_name,
            type=HostType(Pod(namespace=namespace)),
        )
        pod_sid = SId.create_from_service_type(pod_host_type, namespace=namespace)
        pod_dns_name = Name(f"{pod_name}.{namespace}.pod")

        # Bind the pod to its hosting node. If the node was not seen during
        # `_discover_aks_cloud()` (e.g. because the pod is still being
        # scheduled or the node has just been removed), synthesize a
        # placeholder SId so that the graph remains well-formed.
        node_name = spec.get("nodeName") or None
        if node_name:
            if node_name not in self._aks_nodes:
                logger.info(
                    "Pod %s/%s references unknown node '%s'; "
                    "synthesizing placeholder SId.",
                    namespace, pod_name, node_name,
                )
                self._aks_nodes[node_name] = SId(
                    type=ServiceType.get_type_name(ExecutionEnvironment),
                    subtype=ExecutionEnvironmentType.get_type_name(OS),
                    name=node_name,
                )
            self._aks_pods[str(pod_sid)] = self._aks_nodes[node_name]
        else:
            self._aks_pods[str(pod_sid)] = None

        self.services.append(
            Service(
                name=pod_dns_name,
                sid=pod_sid,
                type=ServiceType(pod_host_type),
                subservices=pod_subservices,
                release=metadata.get("resourceVersion"),
            )
        )

    @staticmethod
    def _container_state(status_entry):
        """Extract the high-level state of a container from its status dict."""
        state_dict = status_entry.get("state", {}) or {}
        if "running" in state_dict:
            return "running"
        if "waiting" in state_dict:
            return "waiting"
        if "terminated" in state_dict:
            return "terminated"
        return "unknown"

    # ------------------------------------------------------------------ #
    # Link discovery
    # ------------------------------------------------------------------ #

    def _discover_aks_links_nodes(self):
        """Create hosting links between nodes and the kubelets they run."""
        cloud_services = self.get_services(filter=Cloud)
        kubelet_type = ServiceType.get_type_name(Application)

        for cloud in cloud_services:
            for sub in cloud.subservices:
                if sub.type != kubelet_type:
                    continue

                node = self._aks_nodes.get(sub.domain)
                if node is None:
                    logger.warning(
                        "No node found for kubelet domain '%s'; "
                        "skipping hosting link.", sub.domain,
                    )
                    continue

                peer = Peer(
                    service_name=node.name,
                    sid=node,
                    role=PeerRole.host,
                    consumer=self.get_consumer(sid=node),
                )
                self.links.append(
                    Link(
                        name=sub.name,
                        sid=sub,
                        description=f"{sub.name} hosted on {node}",
                        role=PeerRole.guest,
                        link_type=LinkType.hosting,
                        peers=ArrayOf(Peer)([peer]),
                    )
                )

    def _discover_aks_links_pods(self):
        """Create controlling links between kubelets and the pods they own.

        The kubelet on node N controls every pod whose `spec.nodeName == N`.
        In CTXD terms, the kubelet plays the `control` role and the pod
        plays the `controlled` role.
        """
        cloud_services = self.get_services(filter=Cloud)
        cloud_pods = self.get_services_by_sid(
            SId(
                type=ServiceType.get_type_name(Host),
                subtype=HostType.get_type_name(Pod),
            )
        )
        kubelet_type = ServiceType.get_type_name(Application)

        for cloud in cloud_services:
            for sub in cloud.subservices:
                if sub.type != kubelet_type:
                    continue

                # `sub.domain` is the node name on which this kubelet runs.
                # Build the controlling peer once per kubelet.
                peer = Peer(
                    service_name=sub.name,
                    sid=sub,
                    role=PeerRole.control,
                    consumer=self.get_consumer(sid=sub),
                )

                for pod in cloud_pods:
                    host_node = self._aks_pods.get(str(pod.sid))
                    if host_node is None:
                        continue
                    if host_node.name != sub.domain:
                        continue

                    self.links.append(
                        Link(
                            name=pod.name,
                            sid=pod.sid,
                            description=f"Kubelet controls pod {pod.name}",
                            link_type=LinkType.controlling,
                            role=PeerRole.controlled,
                            peers=ArrayOf(Peer)([peer]),
                        )
                    )