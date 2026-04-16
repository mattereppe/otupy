import ipaddress
import logging
from os import environ

import openstack
from openstack.network.v2.security_group_rule import SecurityGroupRule

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
    actuator_implementation,
)
from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy.profiles.slpf.args import Direction
from otupy.profiles.slpf.profile import Profile

logger = logging.getLogger(__name__)


@actuator_implementation("slpf-openstack")
class SLPFOpenStackActuator(SLPFActuator):
    """OpenStack-based SLPF Actuator implementation."""

    def __init__(self, *, owner, auth, config, platform, db, **kwargs):
        """
        Create an OpenStack-based SLPF actuator.

        :param owner: Owner of the platform.
        :param auth: Authentication parameters.
        :param config: Configuration parameters.
        :param platform: OpenStack platform parameters.
        :param db: Database connection parameters.
        :param kwargs: Additional parameters.
        """
        if environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.owner = owner
            self.auth = auth
            self.config = config
            self.platform = platform
            self.db = db
            self.connection = None
            self.project_id = None

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

            self.connect_to_openstack()

            super().__init__(
                asset_id=owner,
                db_path=db["path"],
                db_name=db["name"],
                db_commands_table_name=db["commands_table_name"],
                db_jobs_table_name=db["jobs_table_name"],
            )

    def connect_to_openstack(self) -> None:
        """Start a connection to OpenStack."""
        try:
            loader = openstack.config.OpenStackConfig(load_yaml_config=False, app_name="unused", app_version="1.0")
            cloud_region = loader.get_one_cloud(
                region_name="",
                auth_type="password",
                auth=self.auth,
                cacert=self.config["cacert"],
            )
            self.connection = openstack.connection.from_config(cloud_config=cloud_region)

            # Get the token from the connection object (it will automatically handle authentication).
            token = self.connection.authorize()

            # Verify successful authentication by checking token.
            if token:
                logger.info("Authentication successful!")
                logger.debug(f"Token: {token}")
            else:
                logger.error("Authentication failed.")

            project = self.connection.identity.find_project(self.auth["project_name"])
            self.project_id = project.id
        except Exception as e:
            logger.error(f"An error occurred: {e}")

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
                custom_data = self.openstack_get_custom_data(target, args["direction"])
                return custom_data
            elif action == Actions.deny or action == Actions.update:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Command not supported.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def execute_allow_command(self, target, direction, custom_data):
        try:
            self.openstack_direction_handler(
                func=self.openstack_allow_handler, target=target, direction=direction, custom_data=custom_data
            )
        except Exception as e:
            raise e

    def openstack_allow_handler(self, target, direction, custom_data):
        """This method handles the execution of OpenC2 `allow` commands for `OpenStack`.

        It maps the OpenC2 `Target` and `direction` argument to the corresponding OpenStack SecurityGroupRule
        and creates it.
        Finally, it associates the security group, where the security rule has been applied, with all the OpenStack ports affected by the security rule.

        :param target: The target of the allow action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to create an ingress or egress traffic rule.
        :type direction: Direction
        :param custom_data: Contains custom data specific to this actuator, previously stored in the database.
        :type custom_data: dict
        """

        try:
            security_group_id = (
                custom_data["ingress_id"] if direction == Direction.ingress else custom_data["egress_id"]
            )
            security_group_rule = self.openstack_from_openc2(target, direction, security_group_id)

            self.connection.network.create_security_group_rule(
                security_group_id=security_group_rule.security_group_id,
                direction=security_group_rule.direction,
                ether_type=security_group_rule.ether_type,
                remote_ip_prefix=security_group_rule.remote_ip_prefix,
                protocol=security_group_rule.protocol,
                port_range_min=security_group_rule.port_range_min,
                port_range_max=security_group_rule.port_range_max,
            )

            cidr = "0.0.0.0/0" if type(target) == IPv4Connection or type(target) == IPv4Net else "::/0"
            if direction == Direction.ingress:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_addr:
                    cidr = target.dst_addr.__str__()
                elif type(target) == IPv4Net or type(target) == IPv6Net:
                    cidr = target.__str__()
            else:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_addr:
                    cidr = target.src_addr.__str__()
            cidr = ipaddress.ip_network(cidr)
            ports = list(self.connection.network.ports(project_id=self.project_id))
            for port in ports:
                for fixed_ip in port.fixed_ips:
                    ip = ipaddress.ip_address(fixed_ip["ip_address"])
                    if ip in cidr:
                        sg_ids = port.security_group_ids
                        if security_group_id not in sg_ids:
                            self.connection.network.update_port(
                                port.id, port_security_enabled=True, security_groups=sg_ids + [security_group_id]
                            )
                            logger.info(
                                "[OPENSTACK] Security group " + security_group_id + " assigned to port " + port.id
                            )
                        break

        except Exception as e:
            raise e

    def execute_delete_command(self, command_to_delete, custom_data):
        try:
            self.openstack_direction_handler(
                func=self.openstack_delete_handler,
                target=command_to_delete.target.getObj(),
                direction=command_to_delete.args["direction"],
                custom_data=custom_data,
            )
        except Exception as e:
            raise e

    def openstack_delete_handler(self, target, direction, custom_data):
        """This method handles the execution of OpenC2 `delete` commands for `OpenStack`.

        Starting from the OpenC2 `Target` and `direction` argument of the command to delete,
        the corresponding OpenStack SecurityGroupRule ID is retrieved.
        The OpenStack SecurityGroupRule is then deleted, unless it is the last rule in the Security Group,
        in which case the entire Security Group is dissociated from the OpenStack ports using it and then deleted.

        :param target: The target of the action to be deleted.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to delete an incoming or outgoing traffic rule.
        :type direction: Direction
        :param custom_data: Contains custom data specific to this actuator, previously stored in the database.
        :type custom_data: dict
        """

        try:
            security_group_id = (
                custom_data["ingress_id"] if direction == Direction.ingress else custom_data["egress_id"]
            )
            rule_id = self.openstack_get_rule_id(target, direction, security_group_id)
            if rule_id:
                rules = list(self.connection.network.security_group_rules(security_group_id=security_group_id))
                if len(rules) == 1 and rules[0].id == rule_id:
                    ports = list(self.connection.network.ports(project_id=self.project_id))
                    for port in ports:
                        if security_group_id in port.security_group_ids:
                            new_sgs = [sg_id for sg_id in port.security_group_ids if sg_id != security_group_id]
                            self.connection.network.update_port(port, security_group_ids=new_sgs)
                    self.connection.network.delete_security_group(security_group_id)
                else:
                    logger.info("[OPENSTACK] Deleting OpenStack rule " + rule_id)
                    self.connection.network.delete_security_group_rule(rule_id)
            else:
                raise ValueError(StatusCode.BADREQUEST, "Security rule not found.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def openstack_direction_handler(self, func, **kwargs):
        """This method handles the direction of OpenC2 `allow` or `delete` commands.

        Executes the function passed as an argument with its kwargs for `ingress`, `egress` or `both` directions.

        :param func: The `OpenStack-based` SLPF Actuator handler method for OpenC2 `allow` or `delete` command.
        :type func: method
        :param kwargs: A dictionary of arguments for the execution of the `OpenStack-based` SLPF Actuator handler method for OpenC2 `allow` or `delete` command.
        :type kwargs: dict
        """
        try:
            if kwargs["direction"] == Direction.both:
                kwargs["direction"] = Direction.ingress
                func(**kwargs)
                kwargs["direction"] = Direction.egress
            func(**kwargs)
        except Exception as e:
            raise e

    def openstack_get_custom_data(self, target, direction):
        """This method retrieves the actuator-specific custom data for OpenStack.

        The custom data includes the ID of the Security Group where the security rule controlling inbound traffic will be inserted
        and the ID of the Security Group where the security rule controlling outbound traffic will be inserted.

        :param target: The target of the allow action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to allow incoming traffic, outgoing traffic or both for the specified target.
        :type direction: Direction

        :return: Actuator-specific custom data to be stored in the database for future function execution
        :rtype: dict
        """

        try:
            custom_data = {"ingress_id": None, "egress_id": None}

            dst_addr = "0.0.0.0/0" if type(target) == IPv4Connection or type(target) == IPv4Net else "::/0"
            src_addr = "0.0.0.0/0" if type(target) == IPv4Connection or type(target) == IPv4Net else "::/0"
            if direction == Direction.ingress or direction == Direction.both:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_addr:
                    dst_addr = target.dst_addr.__str__()
                elif type(target) == IPv4Net or type(target) == IPv6Net:
                    dst_addr = target.__str__()
                custom_data["ingress_id"] = self.openstack_get_security_group_ids(dst_addr, target, Direction.ingress)

            if direction == Direction.egress or direction == Direction.both:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_addr:
                    src_addr = target.src_addr.__str__()
                custom_data["egress_id"] = self.openstack_get_security_group_ids(src_addr, target, Direction.egress)

            return custom_data
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def openstack_get_security_group_ids(self, cidr, target, direction):
        """This method retrieves the ID of the Security Group where a specific rule is to be inserted.
        If the Security Group does not exist, it creates a new one.
        If the Security Group exists, it checks that the security rule is not already present within it.

        :param cidr: Specifies the single IP address or range of IP addresses within the OpenStack network involved in the command.
        :type cidr: str
        :param target: The target of the allow action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to allow incoming traffic, outgoing traffic or both for the specified target.
        :type direction: Direction

        :return: The ID of the Security Group where a specific rule is to be inserted.
        :rtype: str
        """

        try:
            cidr = ipaddress.ip_network(cidr)
            ports = list(self.connection.network.ports(project_id=self.project_id))
            matching_ports = []
            for port in ports:
                for fixed_ip in port.fixed_ips:
                    ip = ipaddress.ip_address(fixed_ip["ip_address"])
                    if ip in cidr:
                        matching_ports.append(port)
                        break
            if not matching_ports:
                raise ValueError(StatusCode.BADREQUEST, f"No port founded for ip address {cidr}")

            sg_name = self.platform["security_group_base_name"] + str(cidr)
            sg = self.connection.network.find_security_group(name_or_id=sg_name, project_id=self.project_id)

            if not sg:
                logger.info("[OPENSTACK] Creating new security group for %s", str(cidr))
                sg_description = self.platform["security_group_base_description"] + f" ({str(cidr)})"
                sg = self.connection.network.create_security_group(
                    name=sg_name, description=sg_description, project_id=self.project_id
                )
                logger.info("[OPENSTACK] Security group id: %s", sg.id)
                logger.info("[OPENSTACK] Security group name: %s", sg.name)

                for rule in self.connection.network.security_group_rules(security_group_id=sg.id):
                    self.connection.network.delete_security_group_rule(rule.id)
            else:
                if self.openstack_get_rule_id(target, direction, sg.id):
                    raise ValueError(StatusCode.BADREQUEST, "Security rule already exists.")

            return sg.id
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def openstack_get_rule_id(self, target, direction, security_group_id):
        """This method gets the OpenStack SecurityGroupRule `ID` of the corresponding OpenStack `SecurityGroupRule`
        that matches the OpenC2 `Target` and `direction` passed as arguments.

        :param target: The desired OpenC2 Target
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: The desired OpenC2 direction
        :type direction: Direction
        :param security_group_id: The ID of the Security Group that contains the security rule
        :type security_group_id: str

        :return: The desired OpenStack SecurityGroupRule `ID`.
        :rtype: str
        """

        try:
            security_group_rule = self.openstack_from_openc2(target, direction, security_group_id)

            rules = self.connection.network.security_group_rules(
                security_group_id=security_group_rule.security_group_id,
                direction=security_group_rule.direction,
                ether_type=security_group_rule.ether_type,
                protocol=security_group_rule.protocol,
            )

            for rule in rules:
                if (
                    rule.remote_ip_prefix == security_group_rule.remote_ip_prefix
                    and rule.port_range_min == security_group_rule.port_range_min
                    and rule.port_range_max == security_group_rule.port_range_max
                ):
                    return rule.id
            return None
        except Exception as e:
            raise e

    def openstack_from_openc2(self, target, direction, security_group_id):
        """This method generates an OpenStack `SecurityGroupRule`.

        Transforms the OpenC2 `Target` and `direction` argument into a valid OpenStack `SecurityGroupRule`.

        :param target: The OpenC2 Target
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: The OpenC2 direction
        :type direction: Direction
        :param security_group_id: The ID of the Security Group where the security rule needs to be inserted
        :type security_group_id: str

        :return: The corresponding OpenStack `SecurityGroupRule`.
        :rtype: SecurityGroupRule
        """

        try:
            security_group_rule = SecurityGroupRule(
                security_group_id=security_group_id,
                direction=direction.name.lower(),
                ether_type="IPv4" if type(target) == IPv4Net or type(target) == IPv4Connection else "IPv6",
                remote_ip_prefix="0.0.0.0/0" if type(target) == IPv4Net or type(target) == IPv4Connection else "::/0",
                protocol=(
                    target.protocol.name.lower()
                    if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol
                    else None
                ),
                port_range_min=None,
                port_range_max=None,
            )

            if type(target) == IPv4Connection or type(target) == IPv6Connection:
                if direction == Direction.ingress:
                    if target.src_addr:
                        security_group_rule.remote_ip_prefix = target.src_addr.__str__()
                    if target.src_port:
                        security_group_rule.port_range_min = target.src_port
                        security_group_rule.port_range_max = target.src_port
                elif direction == Direction.egress:
                    if target.dst_addr:
                        security_group_rule.remote_ip_prefix = target.dst_addr.__str__()
                    if target.dst_port:
                        security_group_rule.port_range_min = target.dst_port
                        security_group_rule.port_range_max = target.dst_port
            elif type(target) == IPv4Net or type(target) == IPv6Net:
                security_group_rule.remote_ip_prefix = target.__str__()

            return security_group_rule
        except Exception as e:
            raise e
