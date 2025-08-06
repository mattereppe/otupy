import logging
import os
import json
import uuid
import ipaddress

from ipaddress import IPv4Network, IPv6Network

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import NetworkSecurityGroup, SecurityRule
from azure.core.exceptions import ResourceNotFoundError

from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy import Feature, Version, Actions, IPv4Net, IPv4Connection , IPv6Net, IPv6Connection, L4Protocol, Binaryx, StatusCode, ArrayOf, ActionTargets, TargetEnum, Nsid, Response, StatusCodeDescription
import otupy.profiles.slpf as slpf 
from otupy.profiles.slpf.profile import Profile
from otupy.profiles.slpf.args import Direction

logger = logging.getLogger(__name__)

class SLPFActuator_azure(SLPFActuator):
    """ `MSAzure-based` SLPF Actuator implementation.

        This class provides an implementation of the `SLPF Actuator` using MS Azure.
    """

    def __init__(self, authentication_file, resource_group_name, network_security_group_name, max_num_security_rules, hostname=None, named_group=None, asset_id=None, asset_tuple=None, db_directory_path=None, db_name=None, db_commands_table_name=None, db_jobs_table_name=None):
        try:
            self.authentication_file = authentication_file
        #   Resource group name
            self.resource_group_name = resource_group_name
        #   Network Security Group name
            self.network_security_group_name = network_security_group_name
            self.max_num_security_rules = max_num_security_rules

            self.OPENC2VERS=Version(1,0)

            self.AllowedCommandTarget = ActionTargets()
            self.AllowedCommandTarget[Actions.query] = [TargetEnum.features]
            self.AllowedCommandTarget[Actions.allow] = [TargetEnum.ipv4_connection, TargetEnum.ipv6_connection, TargetEnum.ipv4_net, TargetEnum.ipv6_net]
            self.AllowedCommandTarget[Actions.deny] = [TargetEnum.ipv4_connection, TargetEnum.ipv6_connection, TargetEnum.ipv4_net, TargetEnum.ipv6_net]
            self.AllowedCommandTarget[Actions.delete] = [TargetEnum[Profile.nsid+':rule_number']]

        #   Connecting to MS Azure
            #self.connect_to_azure()

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
            logger.info("[AZURE] Initialization error: %s", str(e))
            raise e
        

    def connect_to_azure(self):
        try:
            with open(self.authentication_file) as f:
                credentials = json.load(f)
            
        #   Authentication parameters
            tenant_id = credentials["tenantId"]
            client_id = credentials["clientId"]
            client_secret = credentials["clientSecret"]
            subscription_id = credentials["subscriptionId"]
            location = "italynorth" #westeurope
        #   Authentication
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        #   Creating resource group
            resource_client = ResourceManagementClient(credential, subscription_id)
            if not resource_client.resource_groups.check_existence(self.resource_group_name):
                resource_group_params = {"location": location}
                resource_client.resource_groups.create_or_update(self.resource_group_name, resource_group_params)
        
        #   Client for network resources management
            self.network_client = NetworkManagementClient(credential, subscription_id)
        #   Creating the NSG if it does not exist
            try:
                self.network_client.network_security_groups.get(
                    resource_group_name=self.resource_group_name,
                    network_security_group_name=self.network_security_group_name
                )
            except ResourceNotFoundError:
                nsg_params = {"location": location}
                self.nsg = self.network_client.network_security_groups.begin_create_or_update(
                    self.resource_group_name,
                    self.network_security_group_name,
                    parameters=nsg_params
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
            if action == Actions.allow or action == Actions.deny:
                if (type(target) == IPv4Connection or type(target) == IPv6Connection):
                    if target.protocol and target.protocol != L4Protocol.tcp and target.protocol != L4Protocol.udp and target.protocol != L4Protocol.icmp:
                        raise ValueError(StatusCode.NOTIMPLEMENTED, "Provided protocol not implemented for MS Azure.")
                if action == Actions.deny and 'drop_process' in args:
                    raise ValueError(StatusCode.NOTIMPLEMENTED, "Drop process argument not implemented for MS Azure.")
                
                security_rules = self.crea_lista()
            #    security_rules = self.network_client.security_rules.list(self.resource_group, self.nsg_name)
                if len(security_rules) == self.max_num_security_rules:
                    raise ValueError(StatusCode.INTERNALERROR, "Maximum number of security rule inserted.")
            #    if self.azure_find_security_rule(action, target, args['direction'], security_rules):
            #        raise ValueError(StatusCode.BADREQUEST, "Security rule already exists.")
            elif action == Actions.update:
                raise ValueError(StatusCode.NOTIMPLEMENTED, "Update action not implemented for MS Azure.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise e
        

    def execute_allow_command(self, target, direction):
        try:
            self.azure_direction_handler(
                func=self.azure_create_security_rule,
                direction=direction,
                action=Actions.allow,
                target=target
            )
        except Exception as e:
            raise e
        

    def execute_deny_command(self, target, direction, drop_process):
        try:
            self.azure_direction_handler(
                func=self.azure_create_security_rule,
                direction=direction,
                action=Actions.deny,
                target=target
            )
        except Exception as e:
            raise e
        

    def azure_create_security_rule(self, action, target, direction):
        try:
            security_rule = self.azure_from_openc2(
                action=action,
                target=target,
                direction=direction
            )
            security_rule.name = None #self.azure_generate_unique_rule_name()
            security_rule.priority = self.azure_get_priority(security_rule)

            print("INSERTING RULE ", security_rule.priority)

        #    self.network_client.security_rules.begin_create_or_update(
        #        resource_group_name=self.resource_group,
        #        network_security_group_name=self.nsg_name,
        #        security_rule_name=security_rule.name,
        #        security_rule_parameters=security_rule
        #    ).result()
        except Exception as e:
            raise e
        

    def execute_delete_command(self, command_to_delete):
        try:
        #    security_rules = self.network_client.security_rules.list(resource_group_name=self.resource_group, network_security_group_name=self.nsg_name)
            security_rules = self.crea_lista()

            self.azure_direction_handler(
                func=self.azure_delete_security_rule,
                direction=command_to_delete.args['direction'],
                security_rules=security_rules,
                action=command_to_delete.action,
                target=command_to_delete.target.getObj()
            )
        except Exception as e:
            raise e
        

    def azure_delete_security_rule(self, security_rules, action, target, direction):
        try:
            security_rule = self.azure_from_openc2(
                action=action,
                target=target,
                direction=direction
            )

            security_rules = [ rule for rule in security_rules if rule.direction and rule.direction.lower() == security_rule.direction.lower() ]
            security_rules = sorted(security_rules, key=lambda sr: sr.priority if sr.priority else 9999)
            print("DELETING RULE ", security_rule)

            security_rule = self.azure_get_security_rule(security_rule=security_rule, security_rules=security_rules)
            
            if security_rule:
                logger.info("[AZURE] Deleting Azure security rule " + security_rule.name)
        #        self.network_client.security_rules.begin_delete(
        #            resource_group_name=self.resource_group,
        #            network_security_group_name=self.nsg_name,
        #            security_rule_name=security_rule.name
        #        ).result()
            else:
                raise ValueError("[AZURE] Security rule not found.")
            
            self.azure_shift_rules(security_rule, security_rules)
        except Exception as e:
            raise e
        

    def azure_direction_handler(self, func, **kwargs):
        try:
            if kwargs['direction'] == Direction.both:
                kwargs['direction'] = Direction.ingress
                func(**kwargs)
                kwargs['direction'] = Direction.egress
            func(**kwargs)
        except Exception as e:
            raise e
        

    def azure_from_openc2(self, action, target, direction):
    #   Crea una security rule azure meno gli elementi name e priority
        try:           
            security_rule = SecurityRule(
                access=action.__repr__().capitalize(),
                direction="Inbound" if direction == Direction.ingress else "Outbound",
                source_address_prefix=target.src_addr.__str__() if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_addr else "*",
                destination_address_prefix=target.__str__() if type(target) == IPv4Net or type(target) == IPv6Net else "*",
                protocol=target.protocol.name.capitalize() if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.protocol else "*",
                source_port_range=str(target.src_port) if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.src_port else "*",
                destination_port_range=str(target.dst_port) if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_port else "*"
            )

            if (type(target) == IPv4Connection or type(target) == IPv6Connection) and target.dst_addr:                
                security_rule.destination_address_prefix = target.dst_addr.__str__()

            return security_rule
        except Exception as e:
            raise e
        

    def azure_find_security_rule(self, action, target, direction, security_rules):
        try:
            dir = direction
            if direction == Direction.both:
                dir = Direction.ingress
                security_rule = self.azure_from_openc2(action=action, target=target, direction=dir)
                if self.azure_get_security_rule(security_rule=security_rule, security_rules=security_rules):
                    return True
                dir = Direction.egress
            security_rule = self.azure_from_openc2(action=action, target=target, direction=dir)
            if self.azure_get_security_rule(security_rule=security_rule, security_rules=security_rules):
                return True 
            return False
        except Exception as e:
            raise e
        

    def azure_get_security_rule(self, security_rule, security_rules):
        try:
            for rule in security_rules:
                if(
                    rule.direction.lower() == security_rule.direction.lower() and
                    rule.access.lower() == security_rule.access.lower() and
                    rule.source_address_prefix == security_rule.source_address_prefix and
                    rule.destination_address_prefix == security_rule.destination_address_prefix and
                    rule.protocol.lower() == security_rule.protocol.lower() and
                    rule.source_port_range == security_rule.source_port_range and
                    rule.destination_port_range == security_rule.destination_port_range
                ):
                    return rule
            return None
        except Exception as e:
            raise e

    def azure_generate_unique_rule_name(self):
        while True:
            rule_name = str(uuid.uuid4())
            try:
                self.network_client.security_rules.get(self.resource_group_name,
                                                       self.network_security_group_name,
                                                       rule_name)
            except ResourceNotFoundError:
                print("RULE NAMEEE ", rule_name)
                return rule_name
        

    def azure_get_priority(self, security_rule):
        try:
            address_priority = self.azure_get_address_priority(security_rule)
            protocol_priority = self.azure_get_protocol_priority(security_rule)  
            print("ADDR_PRIORITY ", address_priority)
            print("PROT_PRIORITY ", protocol_priority)

        #   Priorità di partenza 
            base_priority = 500 * address_priority + 100 * protocol_priority + 100
        #   Per la priorità data le reti avrebbero 500 priorità, io ne voglio dare solo 100 quindi sottraggo 400 a tutto quello che viene dopo le reti
            if address_priority > 2:
                base_priority -= 400

            security_rules = self.crea_lista()
        #    security_rules = self.network_client.security_rules.list(
        #        resource_group_name=self.resource_group,
        #        network_security_group_name=self.nsg_name
        #    )
        #   Filtro per direzione giusta (direzioni diverse possono avere la stessa priorità)
            security_rules = [ rule for rule in security_rules if rule.direction and rule.direction.lower() == security_rule.direction.lower() ]
            security_rules = sorted(security_rules, key=lambda sr: sr.priority if sr.priority else 9999)

            first_of_this_group = None
            last_of_this_group = None
            priority_hole = None
            precedent_rule = None
            for rule in security_rules:
                rule_addr_priority = self.azure_get_address_priority(rule)
                rule_prot_priority = self.azure_get_protocol_priority(rule)

                if precedent_rule:
                    if (rule.priority - (rule.priority % 100)) > (precedent_rule.priority - (precedent_rule.priority % 100)):
                        if address_priority > rule_addr_priority or (address_priority == rule_addr_priority and protocol_priority > rule_prot_priority):
                            if (self.azure_get_address_priority(precedent_rule) == rule_addr_priority and self.azure_get_protocol_priority(precedent_rule) == rule_prot_priority):
                                base_priority += 100
 
                if address_priority < rule_addr_priority or (address_priority == rule_addr_priority and protocol_priority < rule_prot_priority):
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
                #   Se target non è una rete possiamo interrompere perchè abbiamo trovato il primo buco
                #   Se target è una rete non conta trovare un buco perchè devo inserire regola nel giusto ordine, salvo però la posizione dell'ultimo buco
                    if priority_hole and address_priority != 2:
                        break      
                precedent_rule = rule

            if first_of_this_group:
                print("FIRST OF THIS", first_of_this_group.priority)
            if last_of_this_group:
                print("LAST OF THIS", last_of_this_group.priority)

            if not first_of_this_group:
                return base_priority
            else:
                if not last_of_this_group:
                    last_of_this_group = first_of_this_group
            #   Se non è una rete ritorno subito il primo buco
                if priority_hole and address_priority != 2:
                    return priority_hole
            #   Se spazio finito (100 posti terminati per questo gruppo) ne alloco altri 100
                if not priority_hole and (last_of_this_group.priority + 1) % 100 == 0:
                    rules = [ rule for rule in security_rules if rule.priority and rule.priority > last_of_this_group.priority ]
                    rules.reverse()
                    for rule in rules:
                        print("RULE: ", rule.priority)
                        print("SPOSTO REGOLA DI 100")
                    #    self.azure_update_priority(
                    #        security_rule=rule,
                    #        new_priority= rule.priority + 100
                    #    )
            
                if address_priority != 2:
                    return last_of_this_group.priority + 1
            #   Se è una rete devo trovare il posto giusto    
                else:
                    rules = None
                    mov = None
                    new_cidr = ipaddress.ip_network(security_rule.destination_address_prefix, strict=False)
                    print("NEW CIDR ", new_cidr)
                    rules = [ rule for rule in security_rules if rule.priority and rule.priority >= first_of_this_group.priority and rule.priority <= last_of_this_group.priority ]
                    if priority_hole:
                        rules_after_hole = [ rule for rule in rules if rule.priority and rule.priority > priority_hole ]
                        first_cidr_after_hole = ipaddress.ip_network(rules_after_hole[0].destination_address_prefix, strict=False)
                        if first_cidr_after_hole.prefixlen >= new_cidr.prefixlen:
                            rules = rules_after_hole
                            mov = -1
                        else:
                            rules = [ rule for rule in rules if rule.priority and rule.priority < priority_hole ]
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
                        print("CIDR ", cidr)
                        mov_expression = new_cidr.prefixlen < cidr.prefixlen if mov == -1 else new_cidr.prefixlen > cidr.prefixlen
                        if type(new_cidr) != type(cidr) or (type(new_cidr) == type(cidr) and mov_expression):
                            print("RULE: ", rule.priority)
                            last_priority = rule.priority
                            print("SPOSTO REGOLA DI ", mov)
                        #    self.azure_update_priority(
                        #        security_rule=rule,
                        #        new_priority=rule.priority + mov
                        #    )
                        else:
                            return rule.priority + mov
                    return last_priority                                        
        except Exception as e:
            raise e
        

    def azure_shift_rules(self, security_rule, security_rules):
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
                    if (rule.priority - (rule.priority % 100)) > (precedent_rule.priority - (precedent_rule.priority % 100)):
                        if address_priority > rule_addr_priority or (address_priority == rule_addr_priority and protocol_priority > rule_prot_priority):
                            if (self.azure_get_address_priority(precedent_rule) == rule_addr_priority and self.azure_get_protocol_priority(precedent_rule) == rule_prot_priority):
                                base_priority += 100

                if address_priority < rule_addr_priority or (address_priority == rule_addr_priority and protocol_priority < rule_prot_priority):
                    break
                elif address_priority == rule_addr_priority and protocol_priority == rule_prot_priority:
                    last_priority = rule.priority

                precedent_rule = rule

            print("BASE PRIORITY ", base_priority)
            print("RULE PRIORITY ", security_rule.priority)
            print("LAST PRIORITY ", last_priority)
            
            rules = [ rule for rule in security_rules if rule.priority and rule.priority >= base_priority and rule.priority <= last_priority ]
            last_hundreds = last_priority - (last_priority % 100)
        #   len(rules) - 1 perchè nella lista c'è ancora la regola che abbiamo appena cancellato 
            if last_hundreds != base_priority and len(rules) - 1 <= last_hundreds - base_priority:
                count = 0
                for rule in rules: 
                    print("RULE: ", rule.priority)
                    if rule.priority != security_rule.priority:
                        if rule.priority > base_priority + count:
                            print("SPOSTO REGOLA A BASE PRIORITY + ", count)
                        #    self.azure_update_priority(
                        #        security_rule=rule,
                        #        new_priority=base_priority + count
                        #    )
                        count += 1

                rules = [ rule for rule in security_rules if rule.priority and rule.priority > last_priority ]
                for rule in rules:
                    print("RULE: ", rule.priority)
                    print("SPOSTO REGOLA DI -100")
                #    self.azure_update_priority(
                #        security_rule=rule,
                #        new_priority=rule.priority - 100
                #    )
            else:
                print("NIENTE DA SCALARE")
        except Exception as e:
            raise e
        

    def azure_update_priority(self, security_rule, new_priority):
        try:
            security_rule.priority = new_priority
            self.network_client.security_rules.begin_create_or_update(
                resource_group_name=self.resource_group_name,
                network_security_group_name=self.network_security_group_name,
                security_rule_name=security_rule.name,
                security_rule_parameters=security_rule
            )
        except Exception as e:
            raise e  
        

    def azure_get_address_priority(self, security_rule):
        try:
            address_priority = None
            src_addr = security_rule.source_address_prefix if security_rule.source_address_prefix and security_rule.source_address_prefix != "*" else None
            dst_addr = security_rule.destination_address_prefix if security_rule.destination_address_prefix and security_rule.destination_address_prefix != "*" else None
            
            if dst_addr and src_addr:
                address_priority = 0
            elif dst_addr and not src_addr:
                dst_addr = ipaddress.ip_network(dst_addr, strict=False)
                if (type(dst_addr) == IPv4Network and dst_addr.prefixlen != 32) or (type(dst_addr) == IPv6Network and dst_addr.prefixlen != 128):
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
        try:
            protocol_priority = None
            protocol = security_rule.protocol if security_rule.protocol and security_rule.protocol != "*" else None
            dst_port = security_rule.destination_port_range if security_rule.destination_port_range and security_rule.destination_port_range != "*" else None
            src_port = security_rule.source_port_range if security_rule.source_port_range and security_rule.source_port_range != "*" else None

        #   Le reti con protocol_priority = 0 perche voglio un solo gruppo di 100, non 500 totali come gli altri
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
        

    def crea_lista(self):
        lista = []

        for i in range(100, 190):
            lista.append(SecurityRule(priority=i,
                                      name=str(i),
                                      direction="Inbound",
                                      access="Allow",
                                      destination_address_prefix="172.19.0.1/32",
                                      source_address_prefix="172.19.0.3/32",
                                      protocol="Tcp",
                                      source_port_range="8080",
                                      destination_port_range="8080"
                                      ))

        lista.append(SecurityRule(priority=191,
                                      name=str(191),
                                      direction="Inbound",
                                      access="Allow",
                                      destination_address_prefix="172.19.0.4/32",
                                      source_address_prefix="172.19.0.3/32",
                                      protocol="Tcp",
                                      source_port_range="8080",
                                      destination_port_range="8080"
                                      ))  
        
        for i in range(1100, 1110):
            lista.append(SecurityRule(priority=i,
                                      name=str(i),
                                      direction="Inbound",
                                      access="Allow",
                                      destination_address_prefix="172.19.0.1/32",
                                      ))

            
        return lista