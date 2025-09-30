#!../.oc2-env/bin/python3
from graphviz import Digraph
import json
import logging
import os

import otupy as oc2
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf
from otupy.transfers.http.message import Message

from pymongo import MongoClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))
logger.addHandler(stdout_handler)

edges_set = set()
processed_links_set = set()
nodes_visited = set()

def add_edge(graph, source, target, relationship_type="", dir_type="forward", color="black", fontcolor="black"):
    edge = (source, target, relationship_type, dir_type)
    if edge not in edges_set:
        graph.edge(source, target, label=relationship_type, dir=dir_type, color=color, fontcolor=fontcolor)
        edges_set.add(edge)

def edge_exists(source, target, relationship_type="", dir_type="forward"):
    return (source, target, relationship_type, dir_type) in edges_set

def get_unprocessed_links(links, parent_node):
    unprocessed_links = []
    for it_link in links:
        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)
        if link_key not in processed_links_set:
            unprocessed_links.append(it_link)
    return unprocessed_links

def connect_to_database(username, password, ip, port, database_name, collection_name):
    try:
        client = MongoClient("mongodb://"+ip+":"+str(port)+"/")
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

def recursive_process_links(links, cmd, pf, p, dot, parent_node):
    for it_link in links:
        link_key = (parent_node, it_link.link_type.name, it_link.name.obj)
        if link_key in processed_links_set:
            continue
        processed_links_set.add(link_key)

        for it_peer in it_link.peers:
            peer_hostname = str(it_peer.consumer.server.obj._hostname)
            peer_service_name = str(it_peer.service_name.obj)

            edge_color = "black"
            edge_font_color = "black"
            text_color = None
            font_color = "black"
            if peer_service_name == "slpf":
                edge_color = edge_font_color = text_color = font_color = "red"

            pf['asset_id'] = peer_hostname
            pf.fieldtypes['asset_id'] = peer_hostname
            label = peer_hostname if peer_hostname == peer_service_name else f"{peer_hostname}\n{peer_service_name}"
            dot.node(peer_hostname, label, color=text_color, fontcolor=font_color)

            if not edge_exists(parent_node, peer_hostname):
                add_edge(dot, parent_node, peer_hostname, str(it_link.link_type.name), color=edge_color, fontcolor=edge_font_color)

                tmp_resp = p.sendcmd(cmd)
                logger.info("Got response: %s", tmp_resp)
                #insert_data_database(collection, tmp_resp, peer_hostname)

                if 'results' in tmp_resp.content and 'links' in tmp_resp.content['results']:
                    new_links = tmp_resp.content['results']['links']
                    unprocessed_links = get_unprocessed_links(new_links, peer_hostname)
                    if unprocessed_links:
                        recursive_process_links(unprocessed_links, cmd, pf, p, dot, peer_hostname)

def main(azure_parameters, collection):
    logger.info("Creating Producer for Azure")
    p = oc2.Producer(
        "producer.azure.test",
        JSONEncoder(),
        HTTPTransfer(azure_parameters['ip'], azure_parameters['port'], azure_parameters['endpoint'])
    )

    pf = ctxd.Specifiers({'asset_id': azure_parameters['asset_id']})
    pf.fieldtypes['asset_id'] = azure_parameters['asset_id']
    arg = ctxd.Args({'name_only': False})
    context = ctxd.Context(services=ArrayOf(Name)(), links=ArrayOf(Name)())
    cmd = oc2.Command(action=oc2.Actions.query, target=context, args=arg, actuator=pf)

    resp_azure = p.sendcmd(cmd)
    #insert_data_database(collection, resp_azure, azure_parameters['asset_id'])

    if not arg['name_only']:
        dot = Digraph("azure_graph", graph_attr={'rankdir': 'LR'})
        dot.node('azure', 'Azure Cloud')
        recursive_process_links(resp_azure.content['results']['links'], cmd, pf, p, dot, 'azure')
        dot.render(os.path.dirname(os.path.abspath(__file__))+'/azure_graph', view=False)
        dot.save(os.path.dirname(os.path.abspath(__file__))+'/azure_graph.gv')

if __name__ == '__main__':
    configuration_file = os.path.dirname(os.path.abspath(__file__))+"/azure-configuration.json"
    with open(configuration_file, 'r') as file:
        configuration_parameters = json.load(file)

    collection = connect_to_database(
        username=configuration_parameters['mongodb']['username'],
        password=configuration_parameters['mongodb']['password'],
        ip=configuration_parameters['mongodb']['ip'],
        port=configuration_parameters['mongodb']['port'],
        database_name=configuration_parameters['mongodb']['database_name'],
        collection_name=configuration_parameters['mongodb']['collection_name']
    )

    for element in configuration_parameters['clusters']:
        if element["type"] == "azure":
            main(element, collection)
