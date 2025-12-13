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

logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.DEBUG)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(otupy.LogFormatter(datetime=True,name=True))
hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)

DEFAULT_OPENC2_HTTP_PORT=443
DEFAULT_OPENC2_ENDPOINT="/.well-known/openc2"
DEFAULT_LOOP_FREQUENCY=60 # seconds

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
#def connect_to_database(username, password, ip, port, database_name, collection_name):
#
#        try:
#            client = MongoClient("mongodb://"+ip+":"+str(port)+"/")
#        except Exception:
#            client = MongoClient("mongodb://"+username+":"+password+"@"+ip+":"+str(port)+"/")    
#
#        # Create or switch to a database
#        db = client[database_name]
#
#        # Create or switch to a collection
#        collection = db[collection_name]
#
#        # Delete all documents in the collection
#        collection.delete_many({})
#
#        #return an empty collection
#        return collection 
#
#
#def insert_data_database(collection, response, peer_hostname =None):
#        #if the node is not already visited -> add to the database
#        if peer_hostname not in nodes_visited:
#            m = Message()
#            m.set(response)
#            data = JSONEncoder().encode(m)
#            parsed_data = json.loads(data)
#            #insert only the results into the database
#            result = parsed_data['body']['openc2']['response']['results']['x-ctxd']
#            collection.insert_one(result).inserted_id
#            nodes_visited.add(peer_hostname)
#
#
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
#                insert_data_database(collection, tmp_resp, peer_hostname)
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

def _log_service(s):
	logger.info("Found service: %s", s)

def _log_services(services):
	try:
		for s in services:
			_log_service(s)
	except:
		logger.info("No service")

def _log_link(l):
	logger.info("Found link: %s", l)

def _log_links(links):
	try:
		for l in links:
			_log_link(l)
	except:
		logger.info("No link")

def _log_context(ctx):
	for c in ctx:
		if 'service' in c:
			_log_service(c['service'])
		else:
			_log_link(c['link'])

def parse_and_default(config_file):
	""" Parse config file and assign default values to mising items
	"""

	# Parse the configuration file.
	with open(config_file) as cf:
	    config = safe_load(cf)

	if 'services' in config:
		for service in config["services"]:
			
			try:
				encoder = otupy.Encoders[service['encoding']].value
			except:
				if 'encoding' in service:
					logger.error("No valid encoder: %s", service['encoding'])
				logger.info("Using default encoder: json")
				encoder = otupy.Encoders["json"].value
			service['encoding']=encoder

			try:
				endpoint = service['endpoint']
			except:
				endpoint = DEFAULT_OPENC2_ENDPOINT
			service['endpoint']=endpoint

			try:
				port = service['port']
			except:
				port = DEFAULT_OPENC2_HTTP_PORT

			# Load the transferer (beautiful name, eh?).
			try:
				transferer = otupy.Transfers[service['transfer']](service['host'], port, endpoint)
			except:
				if 'transfer' in service:
					logger.error("No valid transfer: %s", service['transfer'])
				logger.info("Using default transfer: http")
				transferer = otupy.Transfers['http'](service['host'], port, endpoint)
			service['transfer']=transferer

			# Check number of loops
			try:
				loop = config['loop']
			except:
				loop = -1
			config['loop']=loop

			# Check frequency of loops
			try:
				freq = config['frequency']
			except:
				freq = DEFAULT_LOOP_FREQUENCY
			config['frequency']=freq
	else:
		config['service'] = []

	return config


# The loop "decorator", which cannot be used as decorator
# because the two arguments are only known at run-time
def loop(num=0, freq=0):
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
	for r in resource_list:
		res = {}
		res['source'] = root
		res[res_type] = r
		context.append(res)
	return context
	

def discovery(config):
	""" Orchestrate discovery

		Start the discovery process for each root service provided by configuration.
	"""
	ctx = []

	# Start recursive discovery
	for root in config['services']:
		service_list, link_list = discover(root)
		ctx = add_resource(ctx, root, 'service', service_list)
		ctx = add_resource(ctx, root, 'link', link_list)
		# TODO: recursive discovery of peers with valid actuators in links

	_log_context(ctx)

def discover(service):
	""" Query an OpenC2 discovery service

		Get the list of services and links from a context discovery actuator.
		:param service: The endpoint to query from the configuration file.
		:return: service and link lists
	"""
	producer = otupy.Producer("ctxd-discovery.mirandaproject.eu", service['encoding'], service['transfer'])
                                                             
	actuator = ctxd.Specifiers({'asset_id': service['actuator']['asset_id']})
	arg = ctxd.Args({'name_only': False, 'cached': False})
	target = ctxd.Context(services=otupy.ArrayOf(Name)(), links=otupy.ArrayOf(Name)())  # expected all services and links
	cmd = otupy.Command(action=otupy.Actions.query, target=target, args=arg, actuator=actuator)
	context = producer.sendcmd(cmd)
	logger.info("Got context from: %s", context.from_)

	return context.content['results']['services'], context.content['results']['services']


def main() -> None:
	"""
	The main function.
	
	:raise RuntimeError: if something goes wrong
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

						

#    insert_data_database(collection, resp_openstack, openstack_parameters['asset_id'])


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


