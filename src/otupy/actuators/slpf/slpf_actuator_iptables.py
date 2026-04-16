import ipaddress
import logging
import os
import subprocess

from otupy import Actions, IPv4Net, IPv4Connection, IPv6Net, IPv6Connection, StatusCode, actuator_implementation
from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy.profiles.slpf.args import Direction
from otupy.profiles.slpf.data import DropProcess

logger = logging.getLogger(__name__)


@actuator_implementation("slpf-iptables")
class SLPFActuatorIPTables(SLPFActuator):
    """iptables-based SLPF Actuator implementation."""

    def __init__(self, *, owner, platform, db, file, **kwargs):
        """
        Create an Azure-based SLPF actuator.

        :param owner: Owner of the platform.
        :param platform: OpenStack platform parameters.
        :param db: Database connection parameters.
        :param file: File parameters.
        :param kwargs: Additional parameters.
        """
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.owner = owner
            self.platform = platform
            self.db = db
            self.file = file
            self.nsg = None
            self.network_client = None

            #   Creating personalized iptables/ip6tables chains and linking them with iptables/ip6tables chains
            if not self.iptables_existing_chain(self.platform["iptables_cmd"], self.platform["iptables_input_chain_name"]):
                logger.info("[IPTABLES] Creating personalized iptables chain %s", self.platform["iptables_input_chain_name"])
                self.iptables_execute_command(self.platform["iptables_cmd"] + " -N " + self.platform["iptables_input_chain_name"])
            if not self.iptables_find_link(self.platform["iptables_cmd"], "INPUT", self.platform["iptables_input_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking INPUT v4 chain to personalized %s v4 chain", self.platform["iptables_input_chain_name"]
                )
                self.iptables_execute_command(self.platform["iptables_cmd"] + " -A INPUT -j " + self.platform["iptables_input_chain_name"])

            if not self.iptables_existing_chain(self.platform["iptables_cmd"], self.platform["iptables_output_chain_name"]):
                logger.info("[IPTABLES] Creating personalized iptables chain %s", self.platform["iptables_output_chain_name"])
                self.iptables_execute_command(self.platform["iptables_cmd"] + " -N " + self.platform["iptables_output_chain_name"])
            if not self.iptables_find_link(self.platform["iptables_cmd"], "OUTPUT", self.platform["iptables_output_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking OUTPUT v4 chain to personalized %s v4 chain",
                    self.platform["iptables_output_chain_name"],
                )
                self.iptables_execute_command(
                    self.platform["iptables_cmd"] + " -A OUTPUT -j " + self.platform["iptables_output_chain_name"]
                )

            if not self.iptables_existing_chain(self.platform["iptables_cmd"], self.platform["iptables_forward_chain_name"]):
                logger.info("[IPTABLES] Creating personalized iptables chain %s", self.platform["iptables_forward_chain_name"])
                self.iptables_execute_command(self.platform["iptables_cmd"] + " -N " + self.platform["iptables_forward_chain_name"])
            if not self.iptables_find_link(self.platform["iptables_cmd"], "FORWARD", self.platform["iptables_forward_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking FORWARD v4 chain to personalized %s v4 chain",
                    self.platform["iptables_forward_chain_name"],
                )
                self.iptables_execute_command(
                    self.platform["iptables_cmd"] + " -A FORWARD -j " + self.platform["iptables_forward_chain_name"]
                )

            if not self.iptables_existing_chain(self.platform["ip6tables_cmd"], self.platform["iptables_input_chain_name"]):
                logger.info("[IPTABLES] Creating personalized ip6tables chain %s", self.platform["iptables_input_chain_name"])
                self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -N " + self.platform["iptables_input_chain_name"])
            if not self.iptables_find_link(self.platform["ip6tables_cmd"], "INPUT", self.platform["iptables_input_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking INPUT v6 chain to personalized %s v6 chain", self.platform["iptables_input_chain_name"]
                )
                self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -A INPUT -j " + self.platform["iptables_input_chain_name"])

            if not self.iptables_existing_chain(self.platform["ip6tables_cmd"], self.platform["iptables_output_chain_name"]):
                logger.info("[IPTABLES] Creating personalized ip6tables chain %s", self.platform["iptables_output_chain_name"])
                self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -N " + self.platform["iptables_output_chain_name"])
            if not self.iptables_find_link(self.platform["ip6tables_cmd"], "OUTPUT", self.platform["iptables_output_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking OUTPUT v6 chain to personalized %s v6 chain",
                    self.platform["iptables_output_chain_name"],
                )
                self.iptables_execute_command(
                    self.platform["ip6tables_cmd"] + " -A OUTPUT -j " + self.platform["iptables_output_chain_name"]
                )

            if not self.iptables_existing_chain(self.platform["ip6tables_cmd"], self.platform["iptables_forward_chain_name"]):
                logger.info("[IPTABLES] Creating personalized ip6tables chain %s", self.platform["iptables_forward_chain_name"])
                self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -N " + self.platform["iptables_forward_chain_name"])
            if not self.iptables_find_link(self.platform["ip6tables_cmd"], "FORWARD", self.platform["iptables_forward_chain_name"]):
                logger.info(
                    "[IPTABLES] Linking FORWARD v6 chain to personalized %s v6 chain",
                    self.platform["iptables_forward_chain_name"],
                )
                self.iptables_execute_command(
                    self.platform["ip6tables_cmd"] + " -A FORWARD -j " + self.platform["iptables_forward_chain_name"]
                )

            #   Path for iptables/ip6tables files
            #   These files are used by iptables/ip6tables-save and iptables/ip6tables-restore commands
            self.iptables_rules_directory_path = (
                self.file["path"]
                if self.file["path"]
                else os.path.dirname(os.path.abspath(__file__))
            )
            if not os.path.exists(self.iptables_rules_directory_path):
                raise ValueError("Iptables rules files path does not exists")

            #   Creating the files
            self.iptables_rules_v4_filename = (
                self.file["iptables_rules_v4_filename"] if self.file["iptables_rules_v4_filename"] else "iptables_rules.v4"
            )
            ext = os.path.splitext(self.iptables_rules_v4_filename)[1]
            if ext != ".v4":
                raise ValueError("Iptables rules v4 file must have a .v4 extension")
            if not os.path.exists(
                os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v4_filename)
            ):
                logger.info("[IPTABLES] Creating file %s", self.iptables_rules_v4_filename)
                with open(
                    os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v4_filename), "w"
                ) as file:
                    file.write("")

            self.iptables_rules_v6_filename = (
                self.file["iptables_rules_v6_filename"] if self.file["iptables_rules_v6_filename"] else "iptables_rules.v6"
            )
            ext = os.path.splitext(self.iptables_rules_v6_filename)[1]
            if ext != ".v6":
                raise ValueError("Iptables rules v6 file must have a .v6 extension")
            if not os.path.exists(
                os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v6_filename)
            ):
                logger.info("[IPTABLES] Creating file %s", self.iptables_rules_v6_filename)
                with open(
                    os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v6_filename), "w"
                ) as file:
                    file.write("")

            super().__init__(
                asset_id=owner,
                db_path=db["path"],
                db_name=db["name"],
                db_commands_table_name=db["commands_table_name"],
                db_jobs_table_name=db["jobs_table_name"],
            )

    def iptables_existing_chain(self, base_cmd, chain_name):
        """This method checks if a custom iptables v4/v6 chain already exists.

        :param base_cmd: Base command for iptables v4/v6.
        :type base_cmd: str
        :param chain_name: Name of the custom iptables v4/v6 chain.
        :type chain_name: str

        :return: `True` if the custom iptables v4/v6 chain already exists, `False` otherwise.
        :rtype: bool
        """

        try:
            self.iptables_execute_command(base_cmd + " -L " + chain_name)
            return True
        except subprocess.CalledProcessError:
            return False

    def iptables_find_link(self, base_cmd, chain_name, personalized_chain_name):
        """This method checks if a custom iptables v4/v6 chain is linked to its corresponding main chain.

        :param base_cmd: Base command for iptables v4/v6.
        :type base_cmd: str
        :param chain_name: Name of the main iptables v4/v6 chain.
        :type chain_name: str
        :param personalized_chain_name: Name of the custom iptables v4/v6 chain.
        :type personalized_chain_name: str

        :return: `True` if the custom iptables v4/v6 chain is linked to its corresponding main chain, `False` otherwise.
        :rtype: bool
        """

        try:
            cmd = base_cmd.strip().split()
            cmd.append("-S")
            cmd.append(chain_name)
            output = subprocess.check_output(cmd, text=True)
            rules = output.strip().splitlines()
            for rule in rules:
                rule_parts = rule.split()
                if "-j" in rule_parts:
                    j_index = rule_parts.index("-j")
                    if j_index + 1 < len(rule_parts):
                        founded_chain = rule_parts[j_index + 1]
                        if founded_chain == personalized_chain_name:
                            return True
            return False
        except subprocess.CalledProcessError as e:
            raise e
        except Exception as e:
            raise e

    def validate_action_target_args(self, action, target, args):
        try:
            if action == Actions.deny:
                if "drop_process" in args and args["drop_process"] == DropProcess.false_ack:
                    raise ValueError(
                        StatusCode.NOTIMPLEMENTED,
                        "Drop process argument with false ack value not implemented for iptables",
                    )

            if action == Actions.update:
                ext = os.path.splitext(target["name"])[1]
                if ext != ".v4" and ext != ".v6":
                    raise ValueError(StatusCode.BADREQUEST, "File not supported")
            return None
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def execute_allow_command(self, target, direction, custom_data=None):
        try:
            self.iptables_direction_handler(action=Actions.allow, target=target, direction=direction)
        except Exception as e:
            raise e

    def execute_deny_command(self, target, direction, drop_process, custom_data=None):
        try:
            self.iptables_direction_handler(
                action=Actions.deny, target=target, direction=direction, drop_process=drop_process
            )
        except Exception as e:
            raise e

    def execute_delete_command(self, command_to_delete, custom_data=None):
        try:
            args = command_to_delete.args
            drop_process = args["drop_process"] if "drop_process" in args else None

            self.iptables_direction_handler(
                action=Actions.delete,
                target=command_to_delete.target.getObj(),
                direction=command_to_delete.args["direction"],
                drop_process=drop_process,
                action_to_delete=command_to_delete.action,
            )
        except Exception as e:
            raise e

    def iptables_direction_handler(self, **kwargs):
        """This method handles the direction of OpenC2 `allow`, `deny` or `delete` commands and
        the iptables `forward chain`.

        :param kwargs: A dictionary of arguments for the execution of the OpenC2 `allow`, `deny` or `delete` command.
        :type kwargs: dict
        """

        try:
            self.iptables_execution_handler(**kwargs, forward=True)
            if kwargs["direction"] == Direction.both:
                kwargs["direction"] = Direction.ingress
                self.iptables_execution_handler(**kwargs)
                kwargs["direction"] = Direction.egress
            self.iptables_execution_handler(**kwargs)
        except Exception as e:
            raise e

    def iptables_execution_handler(self, **kwargs):
        """This method handles the execution of OpenC2 `allow`, `deny` or `delete` actions for `iptables`.

        It creates the desired iptables command and executes it.

        :param kwargs: A dictionary of arguments for the execution of the OpenC2 `allow`, `deny` or `delete` command.
        :type kwargs: dict
        """

        try:
            cmd = self.iptables_create_command(**kwargs)
            self.iptables_execute_command(cmd)
            logger.info("[IPTABLES] Command executed successfully: %s", cmd)
        except Exception as e:
            logger.info("[IPTABLES] Execution error for command: %s", cmd)
            logger.info("[IPTABLES] Exception: %s", str(e))
            raise e

    def iptables_create_command(
        self, action, target, direction, drop_process=None, action_to_delete=None, forward=False
    ):
        """This method creates an iptables v4/v6 `accept rule`, `drop rule` or `delete rule` command.

        :param action: Command action.
        :type action: Actions
        :param target: Command target.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Command direction.
        :type direction: Direction
        :param drop_process: Specifies how to handle denied packets:
                            `none` drop the packet and do not send any notification to the source of the packet,
                            `reject` drop the packet and send an ICMP host unreachable (or equivalent) to the source of the packet,
                            `false_ack` drop the packet and send a false acknowledgment.
        :type drop_process: DropProcess
        :param action_to_delete: The action of the OpenC2 `Command` to delete (in case of delete command).
        :type action_to_delete: Actions
        :param forward: A flag that specifies if the rule has to be inserted in the iptables forward chain.
        :type forward: bool

        :return: The created `iptables command`.
        :rtype: str
        """

        try:
            if type(target) == IPv4Connection or type(target) == IPv4Net:
                cmd = self.platform["iptables_cmd"] + " "
            elif type(target) == IPv6Connection or type(target) == IPv6Net:
                cmd = self.platform["ip6tables_cmd"] + " "

            if action == Actions.delete:
                cmd += "-D "
            else:
                cmd += "-I "

            if not forward:
                if direction == Direction.ingress:
                    cmd += self.platform["iptables_input_chain_name"] + " "
                elif direction == Direction.egress:
                    cmd += self.platform["iptables_output_chain_name"] + " "
            else:
                cmd += self.platform["iptables_forward_chain_name"] + " "

            if action != Actions.delete:
                position = self.iptables_get_rule_position(target, direction, forward)
                cmd += f"{position} "

            if type(target) == IPv4Connection or type(target) == IPv6Connection:
                if target.protocol:
                    cmd += f"--protocol {target.protocol} "
                if target.src_addr:
                    cmd += f"--source {target.src_addr} "
                if target.src_port:
                    cmd += f"--sport {target.src_port} "
                if target.dst_addr:
                    cmd += f"--destination {target.dst_addr} "
                if target.dst_port:
                    cmd += f"--dport {target.dst_port} "
            elif type(target) == IPv4Net or type(target) == IPv6Net:
                #   The address is always considered as a destination address
                cmd += "--destination " + target.__str__() + " "

            if action == Actions.allow or action_to_delete == Actions.allow:
                iptables_target = "ACCEPT"
            elif action == Actions.deny or action_to_delete == Actions.deny:
                if drop_process == DropProcess.none:
                    iptables_target = "DROP"
                elif drop_process == DropProcess.reject:
                    iptables_target = "REJECT --reject-with icmp-host-unreachable"

            cmd += f"--jump {iptables_target} "
            return cmd
        except Exception as e:
            raise e

    def iptables_get_rule_position(self, target, direction, forward):
        """This method returns the position where the new rule should be inserted in the considered iptables custom chain.

        It compares the specifity of the new rule to be inserted with the specifity of the rules already present.

        :param target: Command target.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Command direction.
        :type direction: Direction
        :param forward: A flag that specifies if the rule has to be inserted in the iptables forward chain.
        :type forward: bool

        :return: The `position` of the new iptables rule.
        :rtype: str
        """

        try:
            target_cidr = None

            prot_specifity = None
            addr_specifity = None
            if type(target) == IPv4Connection or type(target) == IPv6Connection:
                if target.protocol and target.dst_port and target.src_port:
                    prot_specifity = 5
                elif target.protocol and target.dst_port and not target.src_port:
                    prot_specifity = 4
                elif target.protocol and not target.dst_port and target.src_port:
                    prot_specifity = 3
                elif target.protocol and not target.dst_port and not target.src_port:
                    prot_specifity = 2
                elif not target.protocol:
                    prot_specifity = 1

                if target.dst_addr and target.src_addr:
                    addr_specifity = 5
                elif target.dst_addr and not target.src_addr:
                    addr_specifity = 4
                elif not target.dst_addr and target.src_addr:
                    addr_specifity = 3
                elif not target.dst_addr and not target.src_addr:
                    addr_specifity = 1
            elif type(target) == IPv4Net or type(target) == IPv6Net:
                addr_specifity = 2
                prot_specifity = 1
                target_cidr = ipaddress.ip_network(target.__str__(), strict=False)

            if not forward:
                if direction == Direction.ingress:
                    chain = self.platform["iptables_input_chain_name"]
                elif direction == Direction.egress:
                    chain = self.platform["iptables_output_chain_name"]
            else:
                chain = self.platform["iptables_forward_chain_name"]

            cmd = self.platform["iptables_cmd"] if type(target) == IPv4Connection or type(target) == IPv4Net else self.platform["ip6tables_cmd"]
            cmd = cmd.strip().split()
            cmd.append("-S")
            cmd.append(chain)
            output = subprocess.check_output(cmd, text=True)
            rules = output.strip().splitlines()

            pos = 1
            for rule in rules:
                if not rule.startswith("-A"):
                    continue

                rule_cidr = None
                rule_parts = rule.split()

                rule_addr_specifity = None
                if "-d" in rule_parts and "-s" in rule_parts:
                    rule_addr_specifity = 5
                elif "-d" in rule_parts and not "-s" in rule_parts:
                    rule_cidr = ipaddress.ip_network(rule_parts[rule_parts.index("-d") + 1], strict=False)
                    if rule_cidr.prefixlen == 32:
                        rule_addr_specifity = 4
                    else:
                        rule_addr_specifity = 2
                elif not "-d" in rule_parts and "-s" in rule_parts:
                    rule_addr_specifity = 3
                elif not "-d" in rule_parts and not "-s" in rule_parts:
                    rule_addr_specifity = 1

                rule_prot_specifity = None
                if "-p" in rule_parts and "--dport" in rule_parts and "--sport" in rule_parts:
                    rule_prot_specifity = 5
                elif "-p" in rule_parts and "--dport" in rule_parts and not "--sport" in rule_parts:
                    rule_prot_specifity = 4
                elif "-p" in rule_parts and not "--dport" in rule_parts and "--sport" in rule_parts:
                    rule_prot_specifity = 3
                elif "-p" in rule_parts and not "--dport" in rule_parts and not "--sport" in rule_parts:
                    rule_prot_specifity = 2
                elif not "-p" in rule_parts:
                    rule_prot_specifity = 1

                if rule_addr_specifity < addr_specifity or (
                    rule_addr_specifity == addr_specifity and rule_prot_specifity <= prot_specifity
                ):
                    if addr_specifity != 2:
                        return pos
                    else:
                        if rule_addr_specifity == 2:
                            if rule_cidr.prefixlen <= target_cidr.prefixlen:
                                return pos
                        elif rule_addr_specifity < 2:
                            return pos

                pos += 1

            return pos
        except Exception as e:
            raise e

    def save_persistent_commands(self):
        try:
            logger.info("[IPTABLES] Saving iptables v4 rules")
            cmd = (
                self.platform["iptables_cmd"]
                + "-save > "
                + os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v4_filename)
            )
            self.iptables_execute_command(cmd)
            logger.info("[IPTABLES] Saving iptables v6 rules")
            cmd = (
                self.platform["ip6tables_cmd"]
                + "-save > "
                + os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v6_filename)
            )
            self.iptables_execute_command(cmd)
        except Exception as e:
            logger.info("[IPTABLES] An error occurred saving iptables v4/v6 rules: %s", str(e))
            raise e

    def restore_persistent_commands(self):
        try:
            logger.info("[IPTABLES] Restoring iptables v4 rules")
            cmd = (
                self.platform["iptables_cmd"]
                + "-restore < "
                + os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v4_filename)
            )
            self.iptables_execute_command(cmd)
            logger.info("[IPTABLES] Restoring iptables v6 rules")
            cmd = (
                self.platform["ip6tables_cmd"]
                + "-restore < "
                + os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v6_filename)
            )
            self.iptables_execute_command(cmd)
        except Exception as e:
            logger.info("[IPTABLES] An error occurred restoring iptables v4/v6 rules: %s", str(e))
            raise e

    def clean_actuator_rules(self):
        try:
            logger.info("[IPTABLES] Deleting all iptables v4 rules")
            #   Deleting rules from iptables
            cmd = self.platform["iptables_cmd"] + " -F"
            self.iptables_execute_command(cmd)
            #   Linking personalized iptables chains with iptables chains
            self.iptables_execute_command(self.platform["iptables_cmd"] + " -A INPUT -j " + self.platform["iptables_input_chain_name"])
            self.iptables_execute_command(self.platform["iptables_cmd"] + " -A OUTPUT -j " + self.platform["iptables_output_chain_name"])
            self.iptables_execute_command(self.platform["iptables_cmd"] + " -A FORWARD -j " + self.platform["iptables_forward_chain_name"])

            logger.info("[IPTABLES] Deleting all iptables v6 rules")
            #   Deleting rules from ip6tables
            cmd = self.platform["ip6tables_cmd"] + " -F"
            self.iptables_execute_command(cmd)
            #   Linking personalized ip6tables chains with ip6tables chains
            self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -A INPUT -j " + self.platform["iptables_input_chain_name"])
            self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -A OUTPUT -j " + self.platform["iptables_output_chain_name"])
            self.iptables_execute_command(self.platform["ip6tables_cmd"] + " -A FORWARD -j " + self.platform["iptables_forward_chain_name"])
        except Exception as e:
            logger.info("[IPTABLES] An error occurred deleting all iptables v4/v6 rules: %s", str(e))
            raise e

    def execute_update_command(self, name, path):
        try:
            ext = os.path.splitext(name)[1]

            if ext == ".v4":
                destination = os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v4_filename)
            elif ext == ".v6":
                destination = os.path.join(self.iptables_rules_directory_path, self.iptables_rules_v6_filename)

            with open(path, "r") as src, open(destination, "w") as dst:
                dst.write(src.read())

            self.restore_persistent_commands()
        except Exception as e:
            raise e

    def iptables_execute_command(self, cmd):
        """This method executes an iptables v4/v6 command.

        :param cmd: The iptables v4/v6 command to be executed.
        :type cmd: str
        """

        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise e
        except Exception as e:
            raise e
