import ipaddress
import logging
import os
import uuid
from ipaddress import IPv4Network, IPv6Network

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import SecurityRule
from azure.mgmt.resource.resources import ResourceManagementClient

import otupy.profiles.slpf as slpf
from otupy import (
    Feature,
    Version,
    Actions,
    IPv4Net,
    IPv4Connection,
    IPv6Net,
    IPv6Connection,
    L4Protocol,
    StatusCode,
    ArrayOf,
    ActionTargets,
    TargetEnum,
    Nsid,
    Response,
    StatusCodeDescription,
    actuator_implementation,
)
from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy.profiles.slpf.args import Direction
from otupy.profiles.slpf.profile import Profile

logger = logging.getLogger(__name__)


@actuator_implementation("slpf-azure")
class SLPFActuatorAzure(SLPFActuator):
    """Azure-based SLPF Actuator implementation."""

    def __init__(self, *, owner, auth, config, platform, db, **kwargs):
        """
        Create an Azure-based SLPF actuator.

        :param owner: Owner of the platform.
        :param auth: Authentication parameters.
        :param config: Configuration parameters.
        :param platform: OpenStack platform parameters.
        :param db: Database connection parameters.
        :param kwargs: Additional parameters.
        """
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.owner = owner
            self.auth = auth
            self.config = config
            self.platform = platform
            self.db = db
            self.nsg = None
            self.network_client = None

            self.OPENC2VERS = Version(1, 0)

            self.AllowedCommandTarget = ActionTargets()
            self.AllowedCommandTarget[Actions.query] = [TargetEnum.features]
            self.AllowedCommandTarget[Actions.allow] = [
                TargetEnum.ipv4_connection,
                TargetEnum.ipv6_connection,
                TargetEnum.ipv4_net,
                TargetEnum.ipv6_net,
            ]
            self.AllowedCommandTarget[Actions.deny] = [
                TargetEnum.ipv4_connection,
                TargetEnum.ipv6_connection,
                TargetEnum.ipv4_net,
                TargetEnum.ipv6_net,
            ]
            self.AllowedCommandTarget[Actions.delete] = [TargetEnum[Profile.nsid + ":rule_number"]]

            self.connect_to_azure()

            super().__init__(
                asset_id=owner,
                db_path=db["path"],
                db_name=db["name"],
                db_commands_table_name=db["commands_table_name"],
                db_jobs_table_name=db["jobs_table_name"],
            )

    def connect_to_azure(self):
        """MS Azure connection.

        This method retrieves the credentials required to access Azure services using the authentication file
        and initializes the Resource Group and Network Security Group.
        """

        try:
            #   Authentication parameters
            tenant_id = self.auth["tenantId"]
            client_id = self.auth["clientId"]
            client_secret = self.auth["clientSecret"]
            subscription_id = self.auth["subscriptionId"]
            location = self.auth["location"]
            #   Authentication
            credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

            resource_client = ResourceManagementClient(credential, subscription_id)
            if not resource_client.resource_groups.check_existence(self.platform["resource_group_name"]):
                resource_group_params = {"location": location}
                resource_client.resource_groups.create_or_update(
                    self.platform["resource_group_name"], resource_group_params
                )

            self.network_client = NetworkManagementClient(credential, subscription_id)

            try:
                self.network_client.network_security_groups.get(
                    resource_group_name=self.platform["resource_group_name"],
                    network_security_group_name=self.platform["network_security_group_name"],
                )
            except ResourceNotFoundError:
                nsg_params = {"location": location}
                self.nsg = self.network_client.network_security_groups.begin_create_or_update(
                    self.platform["resource_group_name"],
                    self.platform["network_security_group_name"],
                    parameters=nsg_params,
                ).result()

            logger.info("[AZURE] Connection executed successfully")
        except Exception as e:
            logger.info("[AZURE] Connection failed.")
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
            if action == Actions.allow or action == Actions.deny:
                if type(target) == IPv4Connection or type(target) == IPv6Connection:
                    if (
                        target.protocol
                        and target.protocol != L4Protocol.tcp
                        and target.protocol != L4Protocol.udp
                        and target.protocol != L4Protocol.icmp
                    ):
                        raise ValueError(StatusCode.NOTIMPLEMENTED, "Provided protocol not implemented for MS Azure.")
                if action == Actions.deny and "drop_process" in args:
                    raise ValueError(StatusCode.NOTIMPLEMENTED, "Drop process argument not implemented for MS Azure.")
            elif action == Actions.update:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Update action not implemented for MS Azure.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def execute_allow_command(self, target, direction):
        try:
            self.azure_direction_handler(
                func=self.azure_create_security_rule, direction=direction, action=Actions.allow, target=target
            )
        except Exception as e:
            raise e

    def execute_deny_command(self, target, direction, drop_process):
        try:
            self.azure_direction_handler(
                func=self.azure_create_security_rule, direction=direction, action=Actions.deny, target=target
            )
        except Exception as e:
            raise e

    def azure_create_security_rule(self, action, target, direction):
        """This method handles the execution of OpenC2 `allow` and `deny` commands for `MS Azure`.

        It maps the OpenC2 `Action`, `Target` and `direction` argument to the corresponding MS Azure security rule,
        determines the priority for the security rule and then creates it.

        :param action: The action of the OpenC2 Command.
        :type action: Actions
        :param target: The target of the OpenC2 Command.
        :type target: IPv4Specifies whether to create an incoming or outgoing traffic rule.
        :type direction: Direction
        """

        try:
            security_rule = self.azure_from_openc2(action=action, target=target, direction=direction)
            security_rule.name = self.azure_generate_unique_rule_name()
            security_rule.priority = self.azure_get_priority(security_rule)

            self.network_client.security_rules.begin_create_or_update(
                resource_group_name=self.platform["resource_group_name"],
                network_security_group_name=self.platform["network_security_group_name"],
                security_rule_name=security_rule.name,
                security_rule_parameters=security_rule,
            ).result()
        except Exception as e:
            raise e

    def execute_delete_command(self, command_to_delete):
        try:
            # noinspection PyTypeChecker
            self.azure_direction_handler(
                func=self.azure_delete_security_rule,
                direction=command_to_delete.args["direction"],
                action=command_to_delete.action,
                target=command_to_delete.target.getObj(),
            )
        except Exception as e:
            raise e

    def azure_delete_security_rule(self, action, target, direction):
        """This method handles the execution of OpenC2 `delete` commands for `MS Azure`.

        Starting from the OpenC2 `Target` and `direction` argument of the command to delete,
        the corresponding MS Azure security rule is retrieved and deleted.
        Finally, the priorities of the remaining security rules are updated if necessary.

        :param action: The action of the OpenC2 Command to delete.
        :type action: Actions
        :param target: The target of the OpenC2 Command to delete.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to delete an incoming or outgoing traffic rule.
        :type direction: Direction
        """

        try:
            security_rule = self.azure_from_openc2(action=action, target=target, direction=direction)

            security_rules = self.network_client.security_rules.list(
                resource_group_name=self.platform["resource_group_name"],
                network_security_group_name=self.platform["network_security_group_name"],
            )
            security_rules = [
                rule
                for rule in security_rules
                if rule.direction and rule.direction.lower() == security_rule.direction.lower()
            ]
            security_rules = sorted(security_rules, key=lambda sr: sr.priority if sr.priority else 9999)
            security_rule = self.azure_get_security_rule(security_rule=security_rule, security_rules=security_rules)

            if security_rule:
                logger.info("[AZURE] Deleting Azure security rule " + security_rule.name)
                self.network_client.security_rules.begin_delete(
                    resource_group_name=self.platform["resource_group_name"],
                    network_security_group_name=self.platform["network_security_group_name"],
                    security_rule_name=security_rule.name,
                ).result()
            else:
                raise ValueError("[AZURE] Security rule not found.")

            self.azure_shift_rules(security_rule, security_rules)
        except Exception as e:
            raise e

    def azure_direction_handler(self, func, **kwargs):
        """This method handles the direction of OpenC2 `allow`, `deny` or `delete` commands.

        Executes the function passed as an argument with its kwargs for `ingress`, `egress` or `both` directions.

        :param func: The `MSAzure-based` SLPF Actuator handler method for OpenC2 `allow`, `deny` or `delete` command.
        :type func: method
        :param kwargs: A dictionary of arguments for the execution of the `MSAzure-based` SLPF Actuator handler method for OpenC2 `allow`, `deny` or `delete` command.
        :type kwargs: dict
        """

        try:
            if kwargs["direction"] == Direction.both:
                # noinspection PyTypeChecker
                kwargs["direction"] = Direction.ingress
                func(**kwargs)
                # noinspection PyTypeChecker
                kwargs["direction"] = Direction.egress
            func(**kwargs)
        except Exception as e:
            raise e

    def azure_get_security_rule(self, security_rule, security_rules):
        """This method retrieves the Azure security rule from the list of security rules passed as an argument
        that matches the specified Azure security rule.

        :param security_rule: The Azure security rule to be retrieved.
        :type security_rule: SecurityRule
        :param security_rules: The list of Azure security rules.
        :type security_rules: list

        :return: The desired Azure security rule.
        :rtype: SecurityRule
        """

        try:
            for rule in security_rules:
                if (
                    rule.direction.lower() == security_rule.direction.lower()
                    and rule.access.lower() == security_rule.access.lower()
                    and rule.source_address_prefix == security_rule.source_address_prefix
                    and rule.destination_address_prefix == security_rule.destination_address_prefix
                    and rule.protocol.lower() == security_rule.protocol.lower()
                    and rule.source_port_range == security_rule.source_port_range
                    and rule.destination_port_range == security_rule.destination_port_range
                ):
                    return rule
            return None
        except Exception as e:
            raise e

    def azure_generate_unique_rule_name(self):
        """This method generates a unique name for an Azure security rule.

        :return: The generated security rule name.
        :rtype: str
        """

        while True:
            rule_name = str(uuid.uuid4())
            try:
                self.network_client.security_rules.get(
                    self.platform["resource_group_name"], self.platform["network_security_group_name"], rule_name
                )
            except ResourceNotFoundError:
                return rule_name

    def azure_get_priority(self, security_rule):
        """This method computes the proper priority to assign to the Azure security rule that will be created.

        :param security_rule: The Azure security rule that will be created.
        :type security_rule: SecurityRule

        :return: The priority to assign to the Azure security rule.
        :rtype: int
        """

        try:
            address_priority = self.azure_get_address_priority(security_rule)
            protocol_priority = self.azure_get_protocol_priority(security_rule)

            base_priority = 500 * address_priority + 100 * protocol_priority + 100
            if address_priority > 2:
                base_priority -= 400

            security_rules = self.network_client.security_rules.list(
                resource_group_name=self.platform["resource_group_name"],
                network_security_group_name=self.platform["network_security_group_name"],
            )

            security_rules = [
                rule
                for rule in security_rules
                if rule.direction and rule.direction.lower() == security_rule.direction.lower()
            ]
            security_rules = sorted(security_rules, key=lambda sr: sr.priority if sr.priority else 9999)

            first_of_this_group = None
            last_of_this_group = None
            priority_hole = None
            precedent_rule = None
            for rule in security_rules:
                rule_addr_priority = self.azure_get_address_priority(rule)
                rule_prot_priority = self.azure_get_protocol_priority(rule)

                if precedent_rule:
                    if (rule.priority - (rule.priority % 100)) > (
                        precedent_rule.priority - (precedent_rule.priority % 100)
                    ):
                        if address_priority > rule_addr_priority or (
                            address_priority == rule_addr_priority and protocol_priority > rule_prot_priority
                        ):
                            if (
                                self.azure_get_address_priority(precedent_rule) == rule_addr_priority
                                and self.azure_get_protocol_priority(precedent_rule) == rule_prot_priority
                            ):
                                base_priority += 100

                if address_priority < rule_addr_priority or (
                    address_priority == rule_addr_priority and protocol_priority < rule_prot_priority
                ):
                    break
                elif address_priority == rule_addr_priority and protocol_priority == rule_prot_priority:
                    if not first_of_this_group:
                        first_of_this_group = rule
                        if rule.priority % 100 != 0:
                            priority_hole = rule.priority - (rule.priority % 100)
                    else:
                        last_of_this_group = rule
                        if rule.priority - precedent_rule.priority > 1:
                            priority_hole = rule.priority - 1
                    if priority_hole and address_priority != 2:
                        break
                precedent_rule = rule

            if not first_of_this_group:
                return base_priority
            else:
                if not last_of_this_group:
                    last_of_this_group = first_of_this_group
                if priority_hole and address_priority != 2:
                    return priority_hole
                if not priority_hole and (last_of_this_group.priority + 1) % 100 == 0:
                    rules = [
                        rule for rule in security_rules if rule.priority and rule.priority > last_of_this_group.priority
                    ]
                    rules.reverse()
                    for rule in rules:
                        self.azure_update_priority(security_rule=rule, new_priority=rule.priority + 100)

                if address_priority != 2:
                    return last_of_this_group.priority + 1
                else:
                    rules = None
                    mov = None
                    new_cidr = ipaddress.ip_network(security_rule.destination_address_prefix, strict=False)
                    rules = [
                        rule
                        for rule in security_rules
                        if rule.priority
                        and rule.priority >= first_of_this_group.priority
                        and rule.priority <= last_of_this_group.priority
                    ]
                    if priority_hole:
                        rules_after_hole = [rule for rule in rules if rule.priority and rule.priority > priority_hole]
                        first_cidr_after_hole = ipaddress.ip_network(
                            rules_after_hole[0].destination_address_prefix, strict=False
                        )
                        if first_cidr_after_hole.prefixlen >= new_cidr.prefixlen:
                            rules = rules_after_hole
                            mov = -1
                        else:
                            rules = [rule for rule in rules if rule.priority and rule.priority < priority_hole]
                            if not rules:
                                return priority_hole
                            rules.reverse()
                            mov = 1
                    else:
                        rules.reverse()
                        mov = 1

                    last_priority = None
                    for rule in rules:
                        cidr = ipaddress.ip_network(rule.destination_address_prefix, strict=False)
                        mov_expression = (
                            new_cidr.prefixlen < cidr.prefixlen if mov == -1 else new_cidr.prefixlen > cidr.prefixlen
                        )
                        if type(new_cidr) != type(cidr) or (type(new_cidr) == type(cidr) and mov_expression):
                            last_priority = rule.priority
                            self.azure_update_priority(security_rule=rule, new_priority=rule.priority + mov)
                        else:
                            return rule.priority + mov
                    return last_priority
        except Exception as e:
            raise e

    def azure_shift_rules(self, security_rule, security_rules):
        """This method recompacts the priorities of the active Azure security rules due to the removal of a security rule.

        :param security_rule: The deleted Azure security rule
        :type security_rule: SecurityRule
        :param security_rules: The list of active Azure security rules.
        :type security_rules: list
        """

        try:
            address_priority = self.azure_get_address_priority(security_rule)
            protocol_priority = self.azure_get_protocol_priority(security_rule)
            base_priority = 500 * address_priority + 100 * protocol_priority + 100
            if address_priority > 2:
                base_priority -= 400

            last_priority = None
            precedent_rule = None
            for rule in security_rules:
                rule_addr_priority = self.azure_get_address_priority(rule)
                rule_prot_priority = self.azure_get_protocol_priority(rule)

                if precedent_rule:
                    if (rule.priority - (rule.priority % 100)) > (
                        precedent_rule.priority - (precedent_rule.priority % 100)
                    ):
                        if address_priority > rule_addr_priority or (
                            address_priority == rule_addr_priority and protocol_priority > rule_prot_priority
                        ):
                            if (
                                self.azure_get_address_priority(precedent_rule) == rule_addr_priority
                                and self.azure_get_protocol_priority(precedent_rule) == rule_prot_priority
                            ):
                                base_priority += 100

                if address_priority < rule_addr_priority or (
                    address_priority == rule_addr_priority and protocol_priority < rule_prot_priority
                ):
                    break
                elif address_priority == rule_addr_priority and protocol_priority == rule_prot_priority:
                    last_priority = rule.priority
                precedent_rule = rule

            rules = [
                rule
                for rule in security_rules
                if rule.priority and rule.priority >= base_priority and rule.priority <= last_priority
            ]
            last_hundreds = last_priority - (last_priority % 100)
            if last_hundreds != base_priority and len(rules) - 1 <= last_hundreds - base_priority:
                count = 0
                for rule in rules:
                    if rule.priority != security_rule.priority:
                        if rule.priority > base_priority + count:
                            pass
                        #    self.azure_update_priority(
                        #        security_rule=rule,
                        #        new_priority=base_priority + count
                        #    )
                        count += 1

                rules = [rule for rule in security_rules if rule.priority and rule.priority > last_priority]
                for rule in rules:
                    pass
                #    self.azure_update_priority(
                #        security_rule=rule,
                #        new_priority=rule.priority - 100
                #    )

        except Exception as e:
            raise e

    def azure_update_priority(self, security_rule, new_priority):
        """This method updates the priority of a security rule with a new value passed as an argument.

        :param security_rule: The Azure security rule to be updated.
        :type security_rule: SecurityRule
        :param new_priority: The new priority value.
        :type new_priority: int
        """

        try:
            security_rule.priority = new_priority
            self.network_client.security_rules.begin_create_or_update(
                resource_group_name=self.platform["resource_group_name"],
                network_security_group_name=self.platform["network_security_group_name"],
                security_rule_name=security_rule.name,
                security_rule_parameters=security_rule,
            )
        except Exception as e:
            raise e

    def azure_get_address_priority(self, security_rule):
        """This method calculates the level of specificity of an Azure security rule in terms of address (source address, destination address, both, or neither).

        :param security_rule: The security rule in question.
        :type security_rule: SecurityRule

        :return: The address priority of the Azure security rule.
        :rtype: int
        """

        try:
            address_priority = None
            src_addr = (
                security_rule.source_address_prefix
                if security_rule.source_address_prefix and security_rule.source_address_prefix != "*"
                else None
            )
            dst_addr = (
                security_rule.destination_address_prefix
                if security_rule.destination_address_prefix and security_rule.destination_address_prefix != "*"
                else None
            )

            if dst_addr and src_addr:
                address_priority = 0
            elif dst_addr and not src_addr:
                dst_addr = ipaddress.ip_network(dst_addr, strict=False)
                if (type(dst_addr) == IPv4Network and dst_addr.prefixlen != 32) or (
                    type(dst_addr) == IPv6Network and dst_addr.prefixlen != 128
                ):
                    address_priority = 2
                else:
                    address_priority = 1
            elif not dst_addr and src_addr:
                address_priority = 3
            elif not dst_addr and not src_addr:
                address_priority = 4

            return address_priority
        except Exception as e:
            raise e

    def azure_get_protocol_priority(self, security_rule):
        """This method calculates the level of specificity of an Azure security rule in terms of protocol (combination of protocol and source and destionation ports).

        :param security_rule: The security rule in question.
        :type security_rule: SecurityRule

        :return: The protocol priority of the Azure security rule.
        :rtype: int
        """

        try:
            protocol_priority = None
            protocol = security_rule.protocol if security_rule.protocol and security_rule.protocol != "*" else None
            dst_port = (
                security_rule.destination_port_range
                if security_rule.destination_port_range and security_rule.destination_port_range != "*"
                else None
            )
            src_port = (
                security_rule.source_port_range
                if security_rule.source_port_range and security_rule.source_port_range != "*"
                else None
            )

            if (protocol and dst_port and src_port) or self.azure_get_address_priority(security_rule) == 2:
                protocol_priority = 0
            elif protocol and dst_port and not src_port:
                protocol_priority = 1
            elif protocol and not dst_port and src_port:
                protocol_priority = 2
            elif protocol and not dst_port and not src_port:
                protocol_priority = 3
            elif not protocol and not dst_port and not src_port:
                protocol_priority = 4

            return protocol_priority
        except Exception as e:
            raise e

    def azure_from_openc2(self, action, target, direction):
        """This method generates an MS Azure security rule.

        Transforms the OpenC2 `Action`, `Target` and `direction` argument into a valid Azure security rule.

        :param action: The OpenC2 action.
        :type action: Actions
        :param target: The OpenC2 Target.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: The OpenC2 direction.
        :type direction: Direction


        :return: The corresponding MS Azure security rule.
        :rtype: SecurityRule
        """

        try:
            security_rule = SecurityRule(
                access=action.__repr__().capitalize(),
                direction="Inbound" if direction == Direction.ingress else "Outbound",
                source_address_prefix=(
                    target.src_addr.__str__()
                    if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_addr
                    else "*"
                ),
                destination_address_prefix=(
                    target.__str__() if type(target) == IPv4Net or type(target) == IPv6Net else "*"
                ),
                protocol=(
                    target.protocol.name.capitalize()
                    if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol
                    else "*"
                ),
                source_port_range=(
                    str(target.src_port)
                    if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_port
                    else "*"
                ),
                destination_port_range=(
                    str(target.dst_port)
                    if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_port
                    else "*"
                ),
            )

            if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_addr:
                security_rule.destination_address_prefix = target.dst_addr.__str__()

            return security_rule
        except Exception as e:
            raise e
