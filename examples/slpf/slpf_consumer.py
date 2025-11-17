import json
import logging
import os
import sys
import subprocess

import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.actuators.slpf.slpf_actuator import SLPFActuator
from otupy.actuators.slpf.slpf_actuator_iptables import SLPFActuator_iptables
from otupy.actuators.slpf.slpf_actuator_openstack import SLPFActuator_openstack
from otupy.actuators.slpf.slpf_actuator_kubernetes import SLPFActuator_kubernetes
from otupy.actuators.slpf.slpf_actuator_azure import SLPFActuator_azure
import otupy.profiles.slpf as slpf

# Declare the logger name
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))
# Add both handlers to the logger
logger.addHandler(stdout_handler)
# Add file logger
file_handler = logging.FileHandler("server.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True, datefmt='%t'))
logger.addHandler(file_handler)

def main():
    try:
        #read the configuration file
        configuration_file = os.path.dirname(os.path.abspath(__file__))+"/configuration.json"
        with open(configuration_file, 'r') as file:
            configuration_parameters = json.load(file)
        
        

        actuators = {}
        for element in configuration_parameters['slpf_actuators']:
            if (element["type"] == "iptables"):
                actuators[(slpf.Profile.nsid,element['asset_id'])] = SLPFActuator_iptables(
                      hostname = element['hostname'],
                      named_group = element['named_group'],
                      asset_id = element['asset_id'],
                      asset_tuple = element['asset_tuple'],
                      db_directory_path = element['db_directory_path'],
                      db_name = element['db_name'],                     
                      db_commands_table_name = element['db_commands_table_name'],
                      db_jobs_table_name = element['db_jobs_table_name'],
                      update_directory_path = element['update_directory_path'],
                      iptables_rules_directory_path = element['iptables_rules_directory_path'],
                      iptables_rules_v4_filename = element['iptables_rules_v4_filename'],
                      iptables_rules_v6_filename = element['iptables_rules_v6_filename'],
                      iptables_input_chain_name = element['iptables_input_chain_name'],
                      iptables_output_chain_name = element['iptables_output_chain_name'],
                      iptables_forward_chain_name = element['iptables_forward_chain_name'],
                      iptables_cmd = element['iptables_cmd'],
                      ip6tables_cmd = element['ip6tables_cmd']
                )
            elif (element["type"] == "openstack"):
                actuators[(slpf.Profile.nsid,element['asset_id'])] = SLPFActuator_openstack(
                      hostname = element['hostname'],
                      named_group = element['named_group'],
                      asset_id = element['asset_id'],
                      asset_tuple = element['asset_tuple'],
                      db_directory_path = element['db_directory_path'],
                      db_name = element['db_name'],
                      db_commands_table_name = element['db_commands_table_name'],
                      db_jobs_table_name = element['db_jobs_table_name'],
                      environment_variables_file = element['file_environment_variables'],
                      project_name = element['project_name'],
                      security_group_base_name = element['security_group_base_name'],
                      security_group_base_description = element['security_group_base_description']
                )
            elif (element["type"] == "kubernetes"):
                actuators[(slpf.Profile.nsid,element['asset_id'])] = SLPFActuator_kubernetes(
                      hostname = element['hostname'],
                      named_group = element['named_group'],
                      asset_id = element['asset_id'],
                      asset_tuple = element['asset_tuple'],
                      db_directory_path = element['db_directory_path'],
                      db_name = element['db_name'],
                      db_commands_table_name = element['db_commands_table_name'],
                      db_jobs_table_name = element['db_jobs_table_name'],
                      update_directory_path = element['update_directory_path'],
                      config_file = element['config_file'],
                      kube_context = element['kube_context'],
                      namespace=element['namespace'],
                      subnet_base_label_key=element['subnet_base_label_key'],
                      generate_name=element['generate_name']
                )
            elif (element["type"] == "azure"):
                actuators[(slpf.Profile.nsid,element['asset_id'])] = SLPFActuator_azure(
                      hostname = element['hostname'],
                      named_group = element['named_group'],
                      asset_id = element['asset_id'],
                      asset_tuple = element['asset_tuple'],
                      db_directory_path = element['db_directory_path'],
                      db_name = element['db_name'],
                      db_commands_table_name = element['db_commands_table_name'],
                      db_jobs_table_name = element['db_jobs_table_name'],
                      authentication_file = element['authentication_file'],
                      resource_group_name = element['resource_group_name'],
                      network_security_group_name = element['network_security_group_name']
                )
            else:
                raise Exception("SLPF Actuator type not known")

        #-----------------------RUN THE CONSUMER with multiple actuators-----------------------------------------
        c = oc2.Consumer("testconsumer", actuators, JSONEncoder(), HTTPTransfer(configuration_parameters['consumer']['ip'],
                                                                                configuration_parameters['consumer']['port'],
                                                                                configuration_parameters['consumer']['endpoint']))
        c.run()  

    except Exception as e:
        raise e


if __name__ == "__main__":
    main()