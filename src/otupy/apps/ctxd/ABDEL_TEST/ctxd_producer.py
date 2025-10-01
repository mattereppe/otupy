#!/usr/bin/env python3
import os
import json
import logging
from graphviz import Digraph
from pymongo import MongoClient

import otupy as oc2
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf
from otupy.transfers.http.message import Message
from copy import deepcopy
# ====================== Logging setup ======================
logger = logging.getLogger()
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))
logger.addHandler(stdout_handler)

# ====================== Global tracking ======================
edges_set = set()
processed_links_set = set()
nodes_visited = set()

# ====================== Graph helper ======================
def add_edge(graph, source, target, relationship_type="", dir_type="forward", color="black", fontcolor="black"):
    edge = (source, target, relationship_type, dir_type)
    if edge not in edges_set:
        graph.edge(source, target, label=relationship_type, dir=dir_type, color=color, fontcolor=fontcolor)
        edges_set.add(edge)

def edge_exists(source, target, relationship_type="", dir_type="forward"):
    return (source, target, relationship_type, dir_type) in edges_set

def get_unprocessed_links(links, parent_node):
    return [l for l in links if (parent_node, l.link_type.name, l.name.obj) not in processed_links_set]

# ====================== MongoDB ======================
def connect_to_database(username, password, ip, port, database_name, collection_name):
    try:
        client = MongoClient(f"mongodb://{ip}:{port}/")
    except Exception:
        client = MongoClient(f"mongodb://{username}:{password}@{ip}:{port}/")
    db = client[database_name]
    collection = db[collection_name]
    collection.delete_many({})
    return collection

def insert_data_database(collection, response, peer_hostname=None):
    if peer_hostname not in nodes_visited:
        m = Message()
        m.set(response)
        data = JSONEncoder().encode(m)
        parsed_data = json.loads(data)
        result = parsed_data['body']['openc2']['response']['results']['x-ctxd']
        collection.insert_one(result)
        nodes_visited.add(peer_hostname)

from copy import deepcopy

def recursive_process_links(links, base_cmd, base_pf, producer, dot, parent_node):
    for it_link in links:
        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)
        if link_key in processed_links_set:
            continue
        processed_links_set.add(link_key)

        for it_peer in it_link.peers:
            peer_hostname = str(it_peer.consumer.server.obj._hostname)
            peer_service_name = str(it_peer.service_name.obj)

            # Styling
            edge_color = edge_font_color = text_color = font_color = "black"
            if peer_service_name == "slpf":
                edge_color = edge_font_color = text_color = font_color = "red"

            # Node label
            label = peer_hostname if peer_hostname == peer_service_name else f"{peer_hostname}\n{peer_service_name}"
            dot.node(peer_hostname, label, color=text_color, fontcolor=font_color)

            if not edge_exists(parent_node, peer_hostname):
                add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), color=edge_color, fontcolor=edge_font_color)

                # Create a fresh specifier for this peer
                # there was dirty of pf across differen runs
                pf_peer = ctxd.Specifiers({'asset_id': peer_hostname})
                pf_peer.fieldtypes['asset_id'] = peer_hostname

                #  Create a new command for this peer
                cmd_peer = oc2.Command(
                    action=oc2.Actions.query,
                    target=deepcopy(base_cmd.target),  # preserve context
                    args=deepcopy(base_cmd.args),
                    actuator=pf_peer
                )

                # Check actuator availability in a robust way
                if hasattr(it_peer, "consumer") and hasattr(it_peer.consumer, "server"):
                    actuator = getattr(it_peer.consumer.server, "_actuator", None)
                    if actuator and getattr(actuator, "is_available", lambda: False)():
                        tmp_resp = producer.sendcmd(cmd_peer)
                        logger.info("Got response from actuator %s: %s", peer_hostname, tmp_resp)

                        if 'results' in tmp_resp.content and 'links' in tmp_resp.content['results']:
                            new_links = tmp_resp.content['results']['links']
                            unprocessed_links = get_unprocessed_links(new_links, peer_hostname)
                            if unprocessed_links:
                                recursive_process_links(unprocessed_links, cmd_peer, pf_peer, producer, dot, peer_hostname)



# ====================== Main producer routine ======================
def main(cluster_config, collection=None):
    logger.info("Creating Producer for %s", cluster_config['type'])
    producer = oc2.Producer(
        cluster_config['producer_id'],
        JSONEncoder(),
        HTTPTransfer(cluster_config['ip'], cluster_config['port'], cluster_config['endpoint'])
    )

    pf = ctxd.Specifiers({'asset_id': cluster_config['asset_id']})
    pf.fieldtypes['asset_id'] = str
    arg = ctxd.Args({'name_only': False})
    context = ctxd.Context(services=ArrayOf(Name)(), links=ArrayOf(Name)())
    cmd = oc2.Command(action=oc2.Actions.query, target=context, args=arg, actuator=pf)

    response = producer.sendcmd(cmd)
    # insert_data_database(collection, response, cluster_config['asset_id'])

    if not arg['name_only']:
        dot = Digraph(f"{cluster_config['type']}_graph", graph_attr={'rankdir': 'LR'})
        dot.node(cluster_config['type'].capitalize(), f"{cluster_config['type'].capitalize()} Infrastructure")
        if 'results' in response.content and 'links' in response.content['results']:
            recursive_process_links(response.content['results']['links'], cmd, pf, producer, dot, cluster_config['type'])
        dot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{cluster_config['type']}_graph")
        dot.render(dot_path, view=False)
        dot.save(f"{dot_path}.gv")

# ====================== Entry point ======================
if __name__ == '__main__':
    config_file = CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+"/producers-configuration.json"

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Optional MongoDB connection
    # collection = connect_to_database(**config['mongodb'])
    collection = None

    for cluster in config['clusters']:
        main(cluster, collection)
