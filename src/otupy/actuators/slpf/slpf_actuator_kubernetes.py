import ipaddress
import logging
import os

from kubernetes import client, utils
from kubernetes.client import Configuration
from kubernetes.config.kube_config import KubeConfigLoader

import otupy.profiles.slpf as slpf
from otupy import (
    Actions,
    StatusCode,
    IPv4Net,
    IPv4Connection,
    IPv6Net,
    IPv6Connection,
    Response,
    StatusCodeDescription,
    Feature,
    ArrayOf,
    Version,
    Nsid,
    ActionTargets,
    TargetEnum,
    L4Protocol,
    actuator_implementation,
)
from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy.profiles.slpf.args import Direction
from otupy.profiles.slpf.profile import Profile

logger = logging.getLogger(__name__)


@actuator_implementation("slpf-kubernetes")
class SLPFActuatorKubernetes(SLPFActuator):
    """Kubernetes-based SLPF Actuator implementation."""

    def __init__(self, owner, auth, platform, db, file, **kwargs):
        """
        Create a Kubernetes-based SLPF actuator.

        :param owner: Owner of the platform.
        :param auth: Authentication parameters.
        :param platform: Kubernetes platform parameters.
        :param db: Database connection parameters.
        :param kwargs: Additional parameters.
        """
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.owner = owner
            self.platform = platform
            self.auth = auth
            self.context = self.auth["context"]
            self.namespace = self.platform["namespace"]
            del self.platform["namespace"]
            self.subnet_base_label_key = self.platform["subnet_base_label_key"]
            del self.platform["subnet_base_label_key"]
            self.generate_name = self.platform["generate_name"]
            del self.platform["generate_name"]
            self.named_group = self.platform["named_group"]
            del self.platform["named_group"]
            self.db = db
            self.file = file

            self.OPENC2VERS = Version(1, 0)

            self.AllowedCommandTarget = ActionTargets()
            self.AllowedCommandTarget[Actions.query] = [TargetEnum.features]
            self.AllowedCommandTarget[Actions.allow] = [
                TargetEnum.ipv4_connection,
                TargetEnum.ipv6_connection,
                TargetEnum.ipv4_net,
                TargetEnum.ipv6_net,
            ]
            self.AllowedCommandTarget[Actions.delete] = [TargetEnum[Profile.nsid + ":rule_number"]]
            self.AllowedCommandTarget[Actions.update] = [TargetEnum.file]

            #   Connecting to Kubernetes
            self.connect_to_kubernetes()
            #   Initializing SLPF Actuator Manager
            super().__init__(
                named_group=self.named_group,
                asset_id=owner,
                db_path=db["path"],
                db_name=db["name"],
                db_commands_table_name=db["commands_table_name"],
                db_jobs_table_name=db["jobs_table_name"],
                update_path=self.file["path"],
            )

    def connect_to_kubernetes(self):
        """Kubernetes connection."""

        try:
            print("contexts" in self.context)
            loader = KubeConfigLoader(config_dict=self.context)
            config_cls = type.__call__(Configuration)
            loader.load_and_set(config_cls)
            Configuration.set_default(config_cls)

            # Create API clients
            self.core_api = client.CoreV1Api()
            self.networking_api = client.NetworkingV1Api()
            self.api_client = client.ApiClient()

            logger.info("[KUBERNETES] Connection executed successfully")
        except Exception as e:
            logger.info("[KUBERNETES] Connection failed.")
            raise e

    def query_feature(self, cmd):
        try:
            features = {}
            for f in cmd.target.getObj():
                match f:
                    case Feature.versions:
                        features[Feature.versions.name] = ArrayOf(Version)([self.OPENC2VERS])
                    case Feature.profiles:
                        pf = ArrayOf(Nsid)()
                        pf.append(Nsid(slpf.Profile.nsid))
                        features[Feature.profiles.name] = pf
                    case Feature.pairs:
                        features[Feature.pairs.name] = self.AllowedCommandTarget
                    case Feature.rate_limit:
                        return Response(
                            status=StatusCode.NOTIMPLEMENTED, status_text="Feature 'rate_limit' not yet implemented"
                        )
                    case _:
                        return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid feature '" + f + "'")
            res = slpf.Results(features)
            return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)
        except Exception as e:
            raise e

    def validate_action_target_args(self, action, target, args):
        try:
            if action == Actions.allow:
                if type(target) == IPv4Connection or type(target) == IPv6Connection:
                    if (
                        target.protocol
                        and target.protocol != L4Protocol.tcp
                        and target.protocol != L4Protocol.udp
                        and target.protocol != L4Protocol.sctp
                    ):
                        raise ValueError(StatusCode.NOTIMPLEMENTED, "Protocol not supported.")
                custom_data = self.kubernetes_get_custom_data(target, args["direction"])
                return custom_data
            if action == Actions.deny:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Command not supported.")
            elif action == Actions.update:
                ext = os.path.splitext(target["name"])[1]
                if ext != ".yaml":
                    raise ValueError(StatusCode.BADREQUEST, "File not supported")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def execute_allow_command(self, target, direction, custom_data):
        try:
            protocol = (
                target.protocol.name.upper()
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol
                else None
            )
            cidr = None
            port = None
            ports = None

            metadata = client.V1ObjectMeta(generate_name=self.generate_name, namespace=self.namespace)

            if direction == Direction.ingress or direction == Direction.both:
                policy_types = ["Ingress"]
                pod_selector = client.V1LabelSelector(match_labels=custom_data["ingress_label"])
                ingress = None
                _from = None

                if type(target) == IPv4Connection or type(target) == IPv6Connection:
                    if target.src_addr:
                        cidr = target.src_addr.__str__()
                    if target.src_port:
                        port = target.src_port
                    if target.protocol:
                        ports = [client.V1NetworkPolicyPort(protocol=protocol, port=port)]

                if cidr:
                    _from = [client.V1NetworkPolicyPeer(ip_block=client.V1IPBlock(cidr=cidr))]

                if _from or ports:
                    ingress = [client.V1NetworkPolicyIngressRule(_from=_from, ports=ports)]

                network_policy = client.V1NetworkPolicy(
                    metadata=metadata,
                    spec=client.V1NetworkPolicySpec(
                        policy_types=policy_types, ingress=ingress, pod_selector=pod_selector
                    ),
                )

                self.networking_api.create_namespaced_network_policy(namespace=self.namespace, body=network_policy)

            if direction == Direction.egress or direction == Direction.both:
                policy_types = ["Egress"]
                pod_selector = client.V1LabelSelector(match_labels=custom_data["egress_label"])
                egress = None
                to = None
                cidr = None
                port = None
                ports = None

                if type(target) == IPv4Connection or type(target) == IPv6Connection:
                    if target.dst_addr:
                        cidr = target.dst_addr.__str__()
                    if target.dst_port:
                        port = target.dst_port
                    if target.protocol:
                        ports = [client.V1NetworkPolicyPort(protocol=protocol, port=port)]
                else:
                    cidr = target.__str__()

                if cidr:
                    to = [client.V1NetworkPolicyPeer(ip_block=client.V1IPBlock(cidr=cidr))]

                if to or ports:
                    egress = [client.V1NetworkPolicyEgressRule(to=to, ports=ports)]

                network_policy = client.V1NetworkPolicy(
                    metadata=metadata,
                    spec=client.V1NetworkPolicySpec(
                        policy_types=policy_types, egress=egress, pod_selector=pod_selector
                    ),
                )

                self.networking_api.create_namespaced_network_policy(namespace=self.namespace, body=network_policy)

        except Exception as e:
            raise e

    def execute_delete_command(self, command_to_delete, custom_data):
        try:
            target = command_to_delete.target.getObj()
            direction = command_to_delete.args["direction"]

            cidr = None
            protocol = (
                target.protocol.name.upper()
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol
                else None
            )
            port = None

            if direction == Direction.ingress or direction == Direction.both:
                policy_types = ["Ingress"]

                label_cnt = 0
                deleted = False
                label_key, label_value = list(custom_data["ingress_label"].items())[0]
                network_policies = self.networking_api.list_namespaced_network_policy(namespace=self.namespace)
                for policy in network_policies.items:
                    selector = policy.spec.pod_selector
                    if selector.match_labels.get(label_key) != label_value:
                        continue
                    label_cnt += 1
                    if deleted:
                        continue
                    if set(policy.spec.policy_types) != set(policy_types):
                        continue

                    ingress_rule_list = policy.spec.ingress
                    if ingress_rule_list and len(ingress_rule_list) > 1:
                        continue
                    ingress_rule = ingress_rule_list[0] if ingress_rule_list else None

                    if type(target) == IPv4Connection or type(target) == IPv6Connection:
                        if target.src_addr:
                            cidr = target.src_addr.__str__()
                        if target.src_port:
                            port = target.src_port

                    if not self.kubernetes_match_policy(cidr, protocol, port, Direction.ingress, ingress_rule):
                        continue

                    logger.info("[KUBERNETES] Deleting Kubernetes Network Policy " + policy.metadata.name)
                    self.networking_api.delete_namespaced_network_policy(
                        name=policy.metadata.name, namespace=self.namespace, body=client.V1DeleteOptions()
                    )
                    deleted = True

                if not deleted:
                    raise ValueError(StatusCode.INTERNALERROR, "Kubernetes network policy not found.")

                if label_cnt == 1:
                    label_selector = f"{label_key}={label_value}"
                    pods = self.core_api.list_namespaced_pod(namespace=self.namespace, label_selector=label_selector)
                    for pod in pods.items:
                        labels = pod.metadata.labels
                        if label_key in labels and labels[label_key] == label_value:
                            labels[label_key] = None
                            patch = {"metadata": {"labels": labels}}
                            self.core_api.patch_namespaced_pod(
                                name=pod.metadata.name, namespace=self.namespace, body=patch
                            )

            if direction == Direction.egress or direction == Direction.both:
                policy_types = ["Egress"]
                cidr = None
                port = None

                label_cnt = 0
                deleted = False
                label_key, label_value = list(custom_data["egress_label"].items())[0]
                network_policies = self.networking_api.list_namespaced_network_policy(namespace=self.namespace)
                for policy in network_policies.items:
                    selector = policy.spec.pod_selector
                    if selector.match_labels.get(label_key) != label_value:
                        continue
                    label_cnt += 1
                    if deleted:
                        continue
                    if set(policy.spec.policy_types) != set(policy_types):
                        continue

                    egress_rule_list = policy.spec.egress
                    if egress_rule_list and len(egress_rule_list) > 1:
                        continue
                    egress_rule = egress_rule_list[0] if egress_rule_list else None

                    if type(target) == IPv4Connection or type(target) == IPv6Connection:
                        if target.dst_addr:
                            cidr = target.dst_addr.__str__()
                        if target.dst_port:
                            port = target.dst_port
                    elif type(target) == IPv4Net or type(target) == IPv6Net:
                        cidr = target.__str__()

                    if not self.kubernetes_match_policy(cidr, protocol, port, Direction.egress, egress_rule):
                        continue

                    logger.info("[KUBERNETES] Deleting Kubernetes Network Policy " + policy.metadata.name)
                    self.networking_api.delete_namespaced_network_policy(
                        name=policy.metadata.name, namespace=self.namespace, body=client.V1DeleteOptions()
                    )
                    deleted = True

                if not deleted:
                    raise ValueError(StatusCode.INTERNALERROR, "Kubernetes network policy not found.")

                if label_cnt == 1:
                    label_selector = f"{label_key}={label_value}"
                    pods = self.core_api.list_namespaced_pod(namespace=self.namespace, label_selector=label_selector)
                    for pod in pods.items:
                        labels = pod.metadata.labels
                        if label_key in labels and labels[label_key] == label_value:
                            labels[label_key] = None
                            patch = {"metadata": {"labels": labels}}
                            self.core_api.patch_namespaced_pod(
                                name=pod.metadata.name, namespace=self.namespace, body=patch
                            )

        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def kubernetes_get_custom_data(self, target, direction):
        """This method retrieves the actuator-specific custom data for Kubernetes.

        The custom data includes the label to associate with the Network Policy controlling inbound traffic (and the relevant pods)
        and the label to associate with the Network Policy controlling outbound traffic (and the relevant pods).

        :param target: The target of the allow action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to allow incoming traffic, outgoing traffic or both for the specified target.
        :type direction: Direction

        :return: Actuator-specific custom data to be stored in the database for future function execution
        :rtype: dict
        """

        try:
            custom_data = {"ingress_label": None, "egress_label": None}

            dst_addr = "0.0.0.0/0" if type(target) == IPv4Connection or type(target) == IPv4Net else "::/0"
            src_addr = "0.0.0.0/0" if type(target) == IPv4Connection or type(target) == IPv4Net else "::/0"
            if direction == Direction.ingress or direction == Direction.both:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_addr:
                    dst_addr = target.dst_addr.__str__()
                elif type(target) == IPv4Net or type(target) == IPv6Net:
                    dst_addr = target.__str__()
                custom_data["ingress_label"] = self.kubernetes_get_label(dst_addr)

            if direction == Direction.egress or direction == Direction.both:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_addr:
                    src_addr = target.src_addr.__str__()
                custom_data["egress_label"] = self.kubernetes_get_label(src_addr)

            return custom_data
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def kubernetes_get_label(self, cidr):
        """This method creates Kubernetes labels and associates them with the pods affected by the OpenC2 command.

        :param cidr: Specifies the single IP address or range of IP addresses within the Kubernetes cluster network involved in the command.
        :type cidr: str

        :return: The Kubernetes label
        :rtype: dict
        """

        try:
            cidr = ipaddress.ip_network(cidr)
            str_cidr = str(cidr).replace(".", "-")
            str_cidr = str_cidr.replace("/", "-")
            label_key = self.subnet_base_label_key + str_cidr
            label_value = "true"
            found = False

            pods = self.core_api.list_namespaced_pod(self.namespace)
            for pod in pods.items:
                pod_ip = pod.status.pod_ip
                if pod_ip and ipaddress.ip_address(pod_ip) in cidr:
                    if not found:
                        found = True
                    pod_labels = pod.metadata.labels or {}
                    if pod_labels.get(label_key) != label_value:
                        pod_labels[label_key] = label_value
                        patch = {"metadata": {"labels": pod_labels}}
                        self.core_api.patch_namespaced_pod(name=pod.metadata.name, namespace=self.namespace, body=patch)

            if not found:
                raise ValueError(StatusCode.BADREQUEST, f"No pod founded for ip address {cidr}")

            return {label_key: label_value}
        except Exception as e:
            raise e

    def kubernetes_match_policy(self, cidr, protocol, port, direction, policy):
        """This method checks wheter a Kubernetes `network policy` matches the `cidr`, `protocol` and `port` for the specified direction.

        :param cidr: The desired cidr.
        :type cidr: str
        :param protocl: The desired protocol.
        :type protocol: str
        :param port: The desired port.
        :type port: Port
        :param direction: The desired direction.
        :type direction: Direction
        :param policy: The network policy to be checked.
        :type policy: V1NetworkPolicyIngressRule/V1NetworkPolicyEgressRule

        :return: `True` if the Kubernetes network policy matches the cidr, protocol and port for the specified direction.
                `False` otherwise.
        :rtype: bool
        """

        try:
            if not policy and not cidr and not protocol and not port:
                return True
            elif not policy and (cidr or protocol or port):
                return False

            from_or_to = policy._from if direction == Direction.ingress else policy.to
            if (cidr and not from_or_to) or (not cidr and from_or_to):
                return False
            elif cidr and from_or_to:
                if len(from_or_to) > 1:
                    return False
                peer = from_or_to[0]
                if not peer.ip_block:
                    return False
                if peer.ip_block.cidr != cidr:
                    return False

            ports = policy.ports
            if (protocol and not ports) or (not protocol and ports):
                return False
            elif protocol and ports:
                if len(ports) > 1:
                    return False
                prt = ports[0]
                if prt.protocol != protocol:
                    return False
                if port and prt.port != port:
                    return False
            return True
        except Exception as e:
            raise e

    def clean_actuator_rules(self):
        try:
            logger.info("[KUBERNETES] Deleting all Kubernetes network policy.")
            network_policies = self.networking_api.list_namespaced_network_policy(namespace=self.namespace)
            for policy in network_policies.items:
                self.networking_api.delete_namespaced_network_policy(
                    name=policy.metadata.name, namespace=self.namespace, body=client.V1DeleteOptions()
                )
        except Exception as e:
            logger.info("[KUBERNETES] An error occurred deleting all Kubernetes Network Policy: %s", str(e))
            raise e

    def execute_update_command(self, name, path):
        try:
            self.clean_actuator_rules()

            utils.create_from_yaml(k8s_client=self.api_client, yaml_file=path, namespace=self.namespace)
        except Exception as e:
            raise e
