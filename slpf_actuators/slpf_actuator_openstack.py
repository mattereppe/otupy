import logging
import os
import openstack

from openstack.network.v2.security_group_rule import SecurityGroupRule

from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy import Actions, StatusCode, IPv4Net, IPv4Connection, IPv6Net, IPv6Connection, Response, StatusCodeDescription, Feature, ArrayOf, Version, Nsid, ActionTargets, TargetEnum
import otupy.profiles.slpf as slpf 
from otupy.profiles.slpf.profile import Profile
from otupy.profiles.slpf.args import Direction

logger = logging.getLogger(__name__)

class SLPFActuator_openstack(SLPFActuator):
    """ `OpenStack-based` SLPF Actuator implementation.

        This class provides an implementation of the `SLPF Actuator` using OpenStack.
    """

    def __init__(self, file_environment_variables, security_group_id, hostname=None, named_group=None, asset_id=None, asset_tuple=None, db_directory_path=None, db_name=None, db_commands_table_name=None, db_jobs_table_name=None):
        """ Initialization of the `OpenStack-based` SLPF Actuator.

            This method connects to OpenStack and initializes the `SLPF Actuator`.

            :param file_environment_variables: Absolute path of the file containing environment variables for connecting to OpenStack.
            :type file_environment_variables: str
            :param security_group_id: Id of the OpenStack security group to manage.
            :type security_group_id: str
            :param hostname: SLPF Actuator hostname.
            :type hostname: str
            :param named_group: SLPF Actuator group.
            :type named_group: str
            :param asset_id: SLPF Actuator asset id.
            :type asset_id: str
            :param asset_tuple: SLPF Actuator asset tuple.
            :type asset_tuple: str
            :param db_directory_path: sqlite3 database directory path.
            :type db_directory_path: str
            :param db_name: sqlite3 database name.
            :type db_name: str
            :param db_commands_table_name: Name of the `commands` table in the sqlite3 database.
            :type db_commands_table_name: str
            :param db_jobs_table_name: Name of the `APScheduler jobs` table in the sqlite3 database.
            :type db_jobs_table_name: str
        """
        try:
            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                if not file_environment_variables:
                    raise ValueError("Absolute path of evironment variables file must be provided.")
                self.file_environment_variables = file_environment_variables
                if not security_group_id:
                    raise ValueError("Security group id must be provided.")
                self.security_group_id = security_group_id

                self.OPENC2VERS=Version(1,0)

                self.AllowedCommandTarget = ActionTargets()
                self.AllowedCommandTarget[Actions.query] = [TargetEnum.features]
                self.AllowedCommandTarget[Actions.allow] = [TargetEnum.ipv4_connection, TargetEnum.ipv6_connection, TargetEnum.ipv4_net, TargetEnum.ipv6_net]
                self.AllowedCommandTarget[Actions.delete] = [TargetEnum[Profile.nsid+':rule_number']]


            #   Connecting to OpenStack
                self.connect_to_openstack()
            #   Initializing SLPF Actuator
                super().__init__(hostname=hostname,
                                 named_group=named_group,
                                 asset_id=asset_id,
                                 asset_tuple=asset_tuple,
                                 db_directory_path=db_directory_path,
                                 db_name=db_name,
                                 db_commands_table_name=db_commands_table_name,
                                 db_jobs_table_name=db_jobs_table_name)

        except Exception as e:
            logger.info("[OPENSTACK] Initialization error: %s", str(e))
            raise e
        
    
    def connect_to_openstack(self):
        """ OpenStack connection.
        
            This method loads enviroment variables into linux OS to connect to OpenStack  
            and initializes and authorizes the OpenStack connection.
        """
        try:
        #   Load enviroment variables into linux OS to connect to openstack
            if(self.file_environment_variables is not None): #if it is none, it will use the enviroment variables already present in the system
                with open(self.file_environment_variables, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('export '):  # Only process lines starting with 'export'
                        #   Remove 'export ' and split on the first '='
                            line = line[len('export '):]
                            if '=' in line:
                                key, value = line.split('=', 1)
                            #   Strip quotes around the value if they exist
                                value = value.strip('"').strip("'")
                                os.environ[key] = value
        
            # Initialize the OpenStack connection using environment variables
            self.conn = openstack.connect()           
            # Get the token from the connection object (it will automatically handle authentication)
            token = self.conn.authorize()            
            logger.info("[OPENSTACK] Connection executed successfully")   
        except Exception as e:
            logger.info("[OPENSTACK] Connection failed")  
            raise e
        

    def query_feature(self, cmd):
        try:
            features = {}
            for f in cmd.target.getObj():
                match f:
                    case Feature.versions:
                        features[Feature.versions.name]=ArrayOf(Version)([self.OPENC2VERS])	
                    case Feature.profiles:
                        pf = ArrayOf(Nsid)()
                        pf.append(Nsid(slpf.Profile.nsid))
                        features[Feature.profiles.name]=pf
                    case Feature.pairs:
                        features[Feature.pairs.name]=self.AllowedCommandTarget
                    case Feature.rate_limit:
                        return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Feature 'rate_limit' not yet implemented")
                    case _:
                        return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid feature '" + f + "'")
            res = slpf.Results(features)
            return  Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)
        except Exception as e:
            raise e

        
    
    def validate_action_target_args(self, action, target, args):
        try:
            if action == Actions.allow:
                if (type(target) == IPv4Net or type(target) == IPv6Net) and args['direction'] != Direction.egress:
                    raise ValueError(StatusCode.NOTIMPLEMENTED, "Only egress direction is permitted for IPv4Net/IPv6Net in OpenStack.")
                if self.openstack_find_rule(target, args['direction']):
                    raise ValueError(StatusCode.BADREQUEST, "Openstack rule already exists.")
            elif action == Actions.deny:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Deny action not implemented for OpenStack.")
            elif action == Actions.update:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Update action not implemented for OpenStack.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e
        

    def execute_allow_command(self, target, direction):
        try:
            self.openstack_direction_handler(func=self.openstack_allow_handler,
                                             target=target,
                                             direction=direction)
        except Exception as e:
            raise e
        
        
    def openstack_allow_handler(self, target, direction):
        """ This method handles the execution of an OpenC2 `allow` command for `OpenStack`.

            Starting from OpenC2 `Target` and `direction` gets the corresponding OpenStack SecurityGroupRule  
            and creates it.

            :param target: The target of the allow action.
            :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
            :param direction: Specifies whether to allow incoming traffic, outgoing traffic or both for the specified target.
            :type direction: Direction
        """
        try:
            security_group_rule = self.openstack_from_openc2(target, direction)

            self.conn.network.create_security_group_rule(
                security_group_id=security_group_rule.security_group_id,
                direction=security_group_rule.direction,
                ether_type=security_group_rule.ether_type,
                remote_ip_prefix=security_group_rule.remote_ip_prefix,
                protocol= security_group_rule.protocol,
                port_range_min=security_group_rule.port_range_min,
                port_range_max=security_group_rule.port_range_max
            )            
        except Exception as e:
            raise e
        
        
    def execute_delete_command(self, command_to_delete):
        try:
            self.openstack_direction_handler(func=self.openstack_delete_handler,
                                             target=command_to_delete.target.getObj(),
                                             direction=command_to_delete.args['direction'])
        except Exception as e:
            raise e
        

    def openstack_delete_handler(self, target, direction):
        """ This method handles the execution of an OpenC2 `delete` command for `OpenStack`.

            Starting from OpenC2 `Target` and `direction` of the command to delete 
            gets the corresponding OpenStack SecurityGroupRule `id` 
            and deletes the OpenStack SecurityGroupRule.

            :param target: The target of the delete action.
            :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
            :param direction: Specifies whether to delete a rule for incoming traffic, outgoing traffic or both.
            :type direction: Direction
        """
        try:
            rule_id = self.openstack_get_rule_id(target, direction)
            if rule_id:
                logger.info("[OPENSTACK] Deleting OpenStack rule " + rule_id)
                self.conn.network.delete_security_group_rule(rule_id)
        except Exception as e:
            raise e
        
    
    def openstack_direction_handler(self, func, **kwargs):
        """ This method handles the direction of an OpenC2 `allow` or `delete` command.

            Executes the function passed as an argument with its kwargs for `ingress`, `egress` or `both` directions.

            :param func: The `OpenStack-based` SLPF Actuator handler method for OpenC2 `allow` or `delete` command.
            :type func: method
            :param kwargs: A dictionary of arguments for the execution of the `OpenStack-based` SLPF Actuator handler method for OpenC2 `allow` or `delete` command.
            :type kwargs: dict
        """
        try:
            if kwargs['direction'] == Direction.both:
                kwargs['direction'] = Direction.ingress
                func(**kwargs)
                kwargs['direction'] = Direction.egress
            func(**kwargs)
        except Exception as e:
            raise e
        

    def openstack_find_rule(self, target, direction):
        """ This method search for an OpenStack `SecurityGroupRule` that matches the OpenC2 `Target` and `direction` passed as arguments.

            :param target: The desired OpenC2 Target
            :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
            :param direction: The desired OpenC2 direction
            :type direction: Direction

            :return: This method returns `True` if the OpenStack SecurityGroupRule is found, `False` otherwise.
        """
        try:
            dir = direction
            if direction == Direction.both:
                dir = Direction.ingress
                if self.openstack_get_rule_id(target, dir):
                    return True
                dir = Direction.egress

            if self.openstack_get_rule_id(target, dir):
                    return True
            return False
        except Exception as e:
            raise e
        
        
    def openstack_get_rule_id(self, target, direction):
        """ This method gets the OpenStack SecurityGroupRule `id` of the corresponding OpenStack `SecurityGroupRule` that matches the OpenC2 `Target` and `direction` passed as arguments.
        
            :param target: The desired OpenC2 Target
            :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
            :param direction: The desired OpenC2 direction
            :type direction: Direction

            :return: The desired OpenStack SecurityGroupRule `id`.
        """
        try:
            security_group_rule = self.openstack_from_openc2(target, direction)

            rules = self.conn.network.security_group_rules(
                security_group_id=security_group_rule.security_group_id,
                direction=security_group_rule.direction,
                ether_type=security_group_rule.ether_type,
                protocol=security_group_rule.protocol
            )
            
            for rule in rules:
                if (
                    rule.remote_ip_prefix == security_group_rule.remote_ip_prefix and
                    rule.port_range_min == security_group_rule.port_range_min and
                    rule.port_range_max == security_group_rule.port_range_max
                ):
                    return rule.id
        except Exception as e:
            raise e
        
    
    def openstack_from_openc2(self, target, direction):
        """ This method generates an OpenStack `SecurityGroupRule`.
        
            Transforms OpenC2 `Target` and `direction` into a valid OpenStack `SecurityGroupRule`.

            :param target: The desired OpenC2 Target
            :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
            :param direction: The desired OpenC2 direction
            :type direction: Direction

            :return: The corresponding OpenStack `SecurityGroupRule`.
        """
        try:
            security_group_rule = SecurityGroupRule(
                security_group_id=self.security_group_id,
                direction=direction.name.lower(),
                ether_type='IPv4' if type(target) == IPv4Net or type(target) == IPv4Connection else 'IPv6',
                remote_ip_prefix="0.0.0.0/0" if type(target) == IPv4Net or type(target) == IPv4Connection else "::/0",
                protocol= target.protocol.name.lower() if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol else None,
                port_range_min=None,
                port_range_max=None
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
        