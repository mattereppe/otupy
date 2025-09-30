#!../.oc2-env/bin/python3
# Example to use the OpenC2 library with Azure actuator
#
from graphviz import Digraph
import os

import logging
import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console logger
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))
logger.addHandler(stdout_handler)




edges_set = set()  # Track visited edges
processed_links_set = set()  # Track processed links to avoid recursion on the same links
nodes_visited = set() #track all visited nodes

def add_edge(graph, source, target, relationship_type="", dir_type="forward", color="black", fontcolor="black"):
    edge = (source, target, relationship_type, dir_type)
    if edge not in edges_set:
        graph.edge(source, target, label=relationship_type, dir=dir_type, color = color, fontcolor = fontcolor)
        edges_set.add(edge)

def edge_exists(source, target, relationship_type="", dir_type="forward"):
    return (source, target, relationship_type, dir_type) in edges_set

def get_unprocessed_links(links, parent_node):
    """Return only the unprocessed links based on the link's name."""
    unprocessed_links = []
    for it_link in links:
        # Assuming each link has a unique name or identifier we can use
        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)  # Use the link's name in the key
        
        if link_key not in processed_links_set:
            unprocessed_links.append(it_link)
    return unprocessed_links

def recursive_process_links(links, cmd, pf, p, dot, parent_node):
    for it_link in links:
        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)  # Create a unique key for the link

        # Skip if the link has been processed to avoid redundant recursion
        if link_key in processed_links_set:
            continue
        
        # Mark this link as processed
        processed_links_set.add(link_key)

        for it_peer in it_link.peers:
            peer_hostname = str(it_peer.consumer.server.obj._hostname)
            peer_service_name = str(it_peer.service_name.obj)

            #set the style of nodes and edges
            edge_color = "black"
            edge_font_color = "black"
            if(peer_service_name == "slpf"): #all edges for slpf must be red
                edge_color = "red" 
                edge_font_color = "red"

            text_color= None
            font_color = "black"
            if(peer_service_name == "slpf"):
                text_color = "red"
                font_color = "red"

            # Add the node if it doesn't exist
            pf['asset_id'] = peer_hostname
            pf.fieldtypes['asset_id'] = peer_hostname
            if(peer_hostname != peer_service_name):
                dot.node(peer_hostname, peer_hostname + "\n"+peer_service_name, color= text_color, fontcolor=font_color)
            else:
                dot.node(peer_hostname, peer_hostname, color= text_color, fontcolor=font_color)
            # Only process if the edge has not been visited
            if not edge_exists(parent_node, peer_hostname):
                if str(it_link.link_type.name) == 'packet_flow':
                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='both',color=edge_color, fontcolor=edge_font_color)
                elif str(it_link.link_type.name) == 'hosting' and it_peer.role.name == 'host':
                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='back',color=edge_color, fontcolor=edge_font_color)
                elif str(it_link.link_type.name) == 'protect' and it_peer.role.name == 'control':
                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), dir_type='back', color=edge_color, fontcolor=edge_font_color)
                else:
                    add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), color=edge_color, fontcolor=edge_font_color)

                # Send command and log response
                tmp_resp = p.sendcmd(cmd)
                logger.info("Got response: %s", tmp_resp)

                # Safeguard for recursive calls
                if 'results' in tmp_resp.content and 'links' in tmp_resp.content['results']:
                    new_links = tmp_resp.content['results']['links']
                    # Get only the unprocessed links
                    unprocessed_links = get_unprocessed_links(new_links, peer_hostname)
                    # Only recurse if unprocessed links exist
                    if unprocessed_links:
                        recursive_process_links(unprocessed_links, cmd, pf, p, dot, peer_hostname)

    return





def main():

    #start_consumer_azure()

    logger.info("Creating Producer for Azure")

    # Producer che comunica con l’actuator Azure
    p = oc2.Producer("producer.azure.test", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))

    # Actuator profile = Azure (asset_id usato dall’actuator)
    pf = ctxd.Specifiers({'asset_id': 'azure'})

    # Argomenti query → vogliamo informazioni complete
    arg = ctxd.Args({'name_only': False})

    # In questo caso chiediamo tutti i servizi/links noti (Azure Resource Manager)
    context = ctxd.Context(
        services=ArrayOf(Name)(), 
        links=ArrayOf(Name)()
    )

    # Creiamo il comando OpenC2 → query
    cmd = oc2.Command(
        action=oc2.Actions.query,
        target=context,
        args=arg,
        actuator=pf
    )

    logger.info("Sending command to Azure actuator: %s", cmd)

    # Send command to azures
    resp = p.sendcmd(cmd)
    logger.info("Got response from Azure actuator: %s", resp)
    
    


if __name__ == '__main__':
    main()
