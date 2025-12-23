""" Service discovery

	To run the discovery, either download the source code or install from ``PyPI`` (see 
	`setup <https://otupy.readthedocs.io/en/latest/download.html#download-and-setup>`__).

	Run the discovery service: ::

		python3 discovery.py [-c | --config <config.yaml>]

"""
#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
from argparse import ArgumentParser
from glob import glob
from os.path import dirname
from yaml import safe_load
from graphviz import Digraph
import json
import logging
import os
import sys
import time

import otupy 
import otupy.encoders  # Do not remove! It is necessary to find the registered encoders.
import otupy.actuators  # Do not remove! It is necessary to find the registered actuators.

import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
#from otupy.transfers.http.message import Message

from pymongo import MongoClient
from kafka import KafkaProducer

logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(otupy.LogFormatter(datetime=True,name=True))
hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)

JSONSCHEMA = "http://mirandaproject.eu/ctxd/v1.0/schema.json"
""" Json schema id currently used to log context data """
defaults = { # Default values for context discovery operation
				'ctxd': {
					'loop': -1,
					'frequency': 60},
				# Default values for OpenC2 communication
				'openc2': {
					'host': '127.0.0.1',
					'port': 443,
					'endpoint': "/.well-known/openc2",
					'encoding': 'json',
					'transfer': 'http'},
				# Default values for Mongodb connection
				'mongodb': {
					'host': '127.0.0.1',
					'port': 27017,
					'db_name': '',
					'user': None,
					'pass': None},
				# Default values for Kafka 
				'kafka': {
					'host': '127.0.0.1',
					'port': 9092,
					'topic': None,
					'security_protocol': 'PLAINTEXT',
					'sasl_mechanism': None,
					'sasl_plain_username': None,
					'sasl_plain_password': None,
					'ssl_cafile': None,
					'ssl_check_hostname': True
				},
				# Default configuration for file publisher
				'file': {
					'name': 'contextdata.json',
					'path': '.'
				}
}
""" Defaults value to be used for missing input parameters """

def set_defaults(config, type_, param):
	""" Sets default values

		Checks if input parameters have value, and assign a default value in case no value was provided.

		:param config: The dictionary with input config parameter.
		:param type_: The group to which the parameter belongs (check `defaults`). There might be parameters with the same name under different stanzas.
		:param param: The name of the parameter.
		:return: The value to be assigned to the parameter.
	"""

	try:
		if config[param] is not None:
			return config[param]
	except:
		pass

	try:
		logger.info("Using default value %s for %s", defaults[type_][param], param)
		return defaults[type_][param]
	except:
		logger.warn("No default value for: %s/%s", type_, param)
		return None


#edges_set = set()  # Track visited edges
#processed_links_set = set()  # Track processed links to avoid recursion on the same links
#nodes_visited = set() #track all visited nodes
#
#def add_edge(graph, source, target, relationship_type="", dir_type="forward", color="black", fontcolor="black"):
#    edge = (source, target, relationship_type, dir_type)
#    if edge not in edges_set:
#        graph.edge(source, target, label=relationship_type, dir=dir_type, color = color, fontcolor = fontcolor)
#        edges_set.add(edge)
#
#def edge_exists(source, target, relationship_type="", dir_type="forward"):
#    return (source, target, relationship_type, dir_type) in edges_set
#
#def get_unprocessed_links(links, parent_node):
#    """Return only the unprocessed links based on the link's name."""
#    unprocessed_links = []
#    for it_link in links:
#        # Assuming each link has a unique name or identifier we can use
#        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)  # Use the link's name in the key
#        
#        if link_key not in processed_links_set:
#            unprocessed_links.append(it_link)
#    return unprocessed_links
#

def connect_to_publishers(config):

	publishers = {}
	# Publishers will always have default values!
	for name, conf in config['publishers'].items():
		match name:
			case "mongodb":
				try: 
					if conf['user'] is not None and conf['pass'] is not None:
						client = MongoClient("mongodb://"+conf['user']+":"+conf['pass']+"@"+conf['host']+":"+str(conf['port']))
					else:
						client = MongoClient("mongodb://"+conf['host']+":"+str(conf['port']))
					# Create or switch to a database
					publishers['mongodb'] = client[conf['db_name']]
				except Exception as e:
					logger.error("Unable to connect to mongodb: %s", e)
			case "kafka":
				try:
					producer = KafkaProducer(bootstrap_servers = [ conf['host']+":"+str(conf['port']) ],
							client_id = config['name'],
                     sasl_plain_username = conf['sasl_plain_username'],
                     sasl_plain_password = conf['sasl_plain_password'],
                     security_protocol = conf['security_protocol'],
                     sasl_mechanism = conf['sasl_mechanism'],
							ssl_check_hostname=conf['ssl_check_hostname'],
							ssl_cafile='ca-cert')
					publishers['kafka'] = producer
				except Exception as e:
					logger.error("Unable to connect to kafka: %s", e)
			case "file":
				try:
					publishers['file'] = open(conf['path']+"/"+conf['name'], 'a')
				except Exception as e:
					logger.error("Unable to open file: %s, reason: %s", conf['name'], e)
			case _:
				logger.warning("Skipping unsupported db: %s", name)
	
	return publishers

def disconnect_from_publishers(publishers):

	for name, conf in publishers.items():
	
		match name:
			case "mongodb":
				pass
			case "kafka":
				conf.flush()
				conf.close()
			case "file":
				conf.close()
			case _:
				logger.warning("Skipping unsupported publisher: %s", name)



def publish_data(config, ctx):

	publishers = connect_to_publishers(config)

	# TODO: Add metadata about the service which publish data
	ctx['date'] = otupy.DateTime()
	try:
		ctx['creator'] = config['name']
	except:
		ctx['creator'] = "unkwnon"
	ctx['jsonschema'] = JSONSCHEMA

	jsondata = otupy.encoders.JSONEncoder().encode(ctx)

	for name, pub  in publishers.items(): 
		match name:
			case 'mongodb':
				try:
					collection = pub[ config['publishers'][name]['collection'] ]
				except:
					# Default collection name if that provided does not work
					collection = pub["contextdata"]
				# Delete all documents in the collection -- NO MORE NECESSARY, because we use metadata right now
				# collection.delete_many({})
				# Note: otupy encoders return str, so we must convert them to dict
				collection.insert_one(json.loads(jsondata)).inserted_id
			case 'kafka':
				try:
					pub.send(config['publishers'][name]['topic'], value=jsondata.encode('utf-8'))
#	pub.send('demo', b'Hello, Kafka!')
					pub.flush()
				except Exception as e:
					logger.error("Unable to publish data to kafka topic: %s", str(e))
			case 'file':
				try:
					pub.write(jsondata)
				except Exception as e:
					logger.error("Unable to dump data to file: %s", e)
			case _:
				# Unrecognized names have been already pruned in the connect phase
				pass

	disconnect_from_publishers(publishers)
	
	


#def recursive_process_links(links, cmd, pf, p, dot, parent_node):
#    print(">>>>>>>>> processing links with cmd: ", cmd)
#    for it_link in links:
#        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)  # Create a unique key for the link
#
#        # Skip if the link has been processed to avoid redundant recursion
#        if link_key in processed_links_set:
#            continue
#        
#        # Mark this link as processed
#        processed_links_set.add(link_key)
#
#        for it_peer in it_link.peers:
#            peer_hostname = str(it_peer.consumer.server.obj._hostname)
#            peer_service_name = str(it_peer.service_name.obj)
#
#            #set the style of nodes and edges
#            edge_color = "black"
#            edge_font_color = "black"
#            if(peer_service_name == "slpf"): #all edges for slpf must be red
#                edge_color = "red" 
#                edge_font_color = "red"
#
#            text_color= None
#            font_color = "black"
#            if(peer_service_name == "slpf"):
#                text_color = "red"
#                font_color = "red"
#
#            # Add the node if it doesn't exist
#            pf['asset_id'] = peer_hostname
#            if(peer_hostname != peer_service_name):
#                dot.node(peer_hostname, peer_hostname + "\n"+peer_service_name, color= text_color, fontcolor=font_color)
#            else:
#                dot.node(peer_hostname, peer_hostname, color= text_color, fontcolor=font_color)
#            # Only process if the edge has not been visited
#            if not edge_exists(parent_node, peer_hostname):
#                if str(it_link.link_type.name) == 'packet_flow':
#                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='both',color=edge_color, fontcolor=edge_font_color)
#                elif str(it_link.link_type.name) == 'hosting' and it_peer.role.name == 'host':
#                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='back',color=edge_color, fontcolor=edge_font_color)
#                elif str(it_link.link_type.name) == 'protect' and it_peer.role.name == 'control':
#                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='back', color=edge_color, fontcolor=edge_font_color)
#                else:
#                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), color=edge_color, fontcolor=edge_font_color)
#
#                # Send command and log response
#                print(">>>>>>>>> processing links with cmd: ", cmd)
#                tmp_resp = p.sendcmd(cmd)
#                logger.info("Got response: %s", tmp_resp)
#
#                #insert data into database
#                publish_data(collection, tmp_resp, peer_hostname)
#
#                # Safeguard for recursive calls
#                if 'results' in tmp_resp.content and 'links' in tmp_resp.content['results']:
#                    new_links = tmp_resp.content['results']['links']
#                    # Get only the unprocessed links
#                    unprocessed_links = get_unprocessed_links(new_links, peer_hostname)
#                    # Only recurse if unprocessed links exist
#                    if unprocessed_links:
#                        recursive_process_links(unprocessed_links, cmd, pf, p, dot, peer_hostname)
#
#    return
#

def _log_context(ctx):
	""" Debug-only function to check what was reported """
	for type_ in ctx.keys():
		for item in ctx[type_]:
			logger.info("Found %s: %s", type_, item)


def parse_and_default(config_file):
	""" Parse config file and assign default values to mising items
	"""

	# Parse the configuration file.
	with open(config_file) as cf:
	    config = safe_load(cf)

	# Service section (ctxd actuators)
	if 'services' in config and config['services'] is not None:
		for service in config["services"]:
			
			# Load default values for missing parameters
			for p in defaults['openc2'].keys():
				service[p] = set_defaults(service,'openc2',p)

			# Check discovery params
			for p in 'loop', 'frequency':
				config[p] = set_defaults(config, 'ctxd', p)	
	else:
		config['services'] = []

	# Database section:
	if 'publishers' in config:
		for name in config['publishers'].keys():
			if config['publishers'][name] is None:
				config['publishers'][name]={}
			for p in defaults[name].keys():
				config['publishers'][name][p] = set_defaults(config['publishers'][name], name,  p)
	else:
		config['publishers']=None

	return config


# The loop "decorator", which cannot be used as decorator
# because the two arguments are only known at run-time
def loop(num=0, freq=0):
	""" Sort of decorator to manage loops of the main function """
	def decorator(func):
		def wrapper(*args, **kwargs):
			nonlocal num, freq
			while num!=0:
				func(*args, **kwargs)
				num-=1
				if num!=0:
					time.sleep(freq)
			return 
		return wrapper
	return decorator

def add_resource(context, root, res_type, resource_list):
	""" Add discovered service/link to the internal list for publishing """
	if context is None:
		context = []
	for r in resource_list:
		res = {}
		res['source'] = root
		res[res_type] = r
		context.append(res)
	return context
	

def discovery(config):
	""" Orchestrate discovery

		Start the discovery process for each root service provided by configuration.
		TODO: Add a recursive mechanism to discover new services found in `Links`.

		:param config: A dictionary reporting the known list of services to discover.
		:return: None. Data are directly inserted in the output sinks.
	"""
	ctx = {'services': None, 'links': None}

	# Start recursive discovery
	for root in config['services']:
		service_list, link_list = discover(root)
		ctx['services'] = add_resource(ctx['services'], root, 'service', service_list)
		ctx['links'] = add_resource(ctx['links'], root, 'link', link_list)
		# TODO: recursive discovery of peers with valid actuators in links

	_log_context(ctx)
	publish_data(config, ctx)

def discover(service):
	""" Query an OpenC2 discovery service

		Get the list of services and links from a context discovery actuator.
		:param service: The endpoint to query from the configuration file.
		:return: service and link lists
	"""
	try:
		encoder = otupy.Encoders[service['encoding']].value
	except:
		service['encoding'] = set_defaults(service, 'openc2', 'encoding')
		logger.error("No valid encoder: %s", service['encoding'])
		logger.info("Using default encoder: %s", )
		encoder = otupy.Encoders[service['encoding']].value

	# Load the transferer (beautiful name, eh?).
	try:
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])
	except:
		service['transfer'] = set_defaults(service, 'openc2', 'transfer')
		logger.error("No valid transfer: %s", service['transfer'])
		logger.info("Using default transfer: %s", service['transfer'])
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])


	producer = otupy.Producer("ctxd-discovery.mirandaproject.eu", encoder, transferer)
                                                             
	actuator = ctxd.Specifiers({'asset_id': service['actuator']['asset_id']})
	arg = ctxd.Args({'name_only': False, 'cached': False})
	target = ctxd.Context(services=otupy.ArrayOf(Name)(), links=otupy.ArrayOf(Name)())  # expected all services and links
	cmd = otupy.Command(action=otupy.Actions.query, target=target, args=arg, actuator=actuator)
	context = producer.sendcmd(cmd)
	logger.info("Got context from: %s", context.from_)

	return context.content['results']['services'], context.content['results']['links']


def main() -> None:
	"""
		The main function

		Loads configuration file, parses it, and run the discovery loop.
	
	"""
	
	# Parse the CLI arguments.
	arguments = ArgumentParser()
	arguments.add_argument("-c", "--config", default=f"{dirname(__file__)}/discovery.yaml",
	                       help="path to the configuration file")
	args = arguments.parse_args()
	
	config = parse_and_default(args.config)

	# Set loop and frequency of the discovery process
	repeat_discovery = loop(config['loop'],config['frequency'])(discovery)
	repeat_discovery(config)

						



#    if not arg['name_only']: #explore actuators only if it is false
#        dot = Digraph("example_graph", graph_attr={'rankdir': 'LR'})
#        dot.node('openstack', 'OpenStack')
## TODO: Add recursive discovery of links
##        recursive_process_links(resp_openstack.content['results']['links'], cmd, pf, p, dot, 'openstack')
#
#        with dot.subgraph() as s:
#            s.attr(rank='min')
#            s.node('os-fw')
#            s.node('kubernetes')
#            s.node('openstack')
#    
#        with dot.subgraph() as s:
#            s.attr(rank='same')
#            s.node('kube-fw')
#            s.node('kube0')
#            s.node('kube1')
#            s.node('kube2')
#
#
#        dot.render(os.path.dirname(os.path.abspath(__file__))+'/example_graph' , view=False)
#        dot.save(os.path.dirname(os.path.abspath(__file__))+'/example_graph.gv')


if __name__ == "__main__":
	main()


