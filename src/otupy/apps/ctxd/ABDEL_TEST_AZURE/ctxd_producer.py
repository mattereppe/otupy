#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
from graphviz import Digraph
import json
import logging
import os
import sys

import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf
from otupy.transfers.http.message import Message

from pymongo import MongoClient

logger = logging.getLogger()
# Set logging level for visibility (INFO for debugging, WARNING for production)
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))
hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)

# --- GLOBAL SETS FOR GRAPH TRACKING ---
edges_set = set()  # Track visited edges (source, target, label, dir)
processed_links_set = set()  # Track processed links to avoid recursion on the same links (parent_id, link_type, link_name)
nodes_visited = set() # Track all visited nodes (sanitized_id) - Acts as Actuator processed filter

# --- HELPER FUNCTIONS FOR SANITIZATION AND LABELING ---

def sanitize_node_id(name):
    """
    Sanitizes the string to be used as a valid Graphviz node ID.
    This resolves the 'Warning: node... unrecognized' errors caused by special characters.
    """
    # Removes spaces, "/", ":", "(", ")", "*", etc. and replaces with '_' or '-'
    return name.replace(' ', '_').replace('/', '_').replace(':', '_').replace('.', '-').replace('*', 'ANY').replace('(', '').replace(')', '').replace('\\', '').replace('[', '').replace(']', '')

def is_nsg_rule_link(link):
    """
    Checks if a link models the parent-child arc between an NSG and its rule,
    identified by 'protect' type and containing '_contains_' in the link name.
    """
    # Check 1: Link type must be 'protect'
    if str(link.link_type.name) != 'protect':
        return False
        
    # Check 2: The link name must explicitly indicate the parent-child relationship
    if '_contains_' not in link.name.obj:
        return False
        
    # Check 3 (Safety check): At least one peer must be an NSG Rule
    if not any('Rule:' in str(p.service_name.obj) for p in link.peers):
        return False
        
    return True

def extract_rule_label(peer_service_name):
    """
    Extracts the action and protocol/port from the rule's descriptive service name 
    to be used as the edge label.
    Expected format: '{NSG} Rule: P{Prio} {ACCESS} {DIRECTION} {PROTO}/{PORT}'
    """
    if 'Rule:' in peer_service_name:
        try:
            # Split the string after "Rule:"
            rule_details = peer_service_name.split('Rule:')[1].strip()
            # Example: "P100 ALLOW INBOUND TCP/443"
            parts = rule_details.split(' ')
            
            # parts[1] is ACCESS (ALLOW/DENY), parts[2] is DIRECTION (INBOUND/OUTBOUND)
            # parts[3] is PROTOCOL/PORT
            access_dir = f"{parts[1].upper()} {parts[2].upper()}"
            proto_port = f"({parts[3]})"
            
            # Return a clean label for the edge
            return f"{access_dir}\n{proto_port}"
        except IndexError:
            return "protect"
    return "protect"

def get_node_attributes(service_name):
    """
    Infers the resource type and creates attributes (label, shape, color) 
    to improve graph readability.

    Returns: 
        tuple: (clean_label, shape, color)
    """
    if 'Rule:' in service_name:
        # Node Style for NSG Rule
        return service_name.split('Rule:')[1].strip(), "box", "darkgreen"

    concise_name = service_name
    lower_name = service_name.lower()
    resource_type = "Azure Resource"
    shape = "box"
    color = "black"

    # --- Specific Network Component Checks ---
    if 'nic' in lower_name and '.' in service_name:
        resource_type = "Network Interface"
        name_parts = service_name.split('.nic.')
        if len(name_parts) > 0 and len(name_parts[0]) > 0:
            concise_name = name_parts[0]
        shape = "ellipse"
        color = "darkblue"
            
    elif 'vpn' in lower_name and 'gw' in lower_name:
        resource_type = "VPN Gateway"
        shape = "octagon"
        color = "purple"
    elif 'nsg' in lower_name and 'agentpool' in lower_name:
        resource_type = "AKS Node NSG"
        shape = "doubleoctagon"
        color = "darkred"
    elif 'nsg' in lower_name:
        resource_type = "Network Security Group"
        shape = "doubleoctagon"
        color = "darkred"
    elif 'vnet' in lower_name or 'vn_' in lower_name:
        resource_type = "Virtual Network"
        shape = "cylinder"
        color = "darkgreen"
    
    # --- Compute/Compute-like Checks (Last to avoid false positives) ---
    elif 'vm' in lower_name or 'apiserver' in lower_name or 'kubernetes' in lower_name or (len(lower_name.split('.')) == 1 and len(service_name) < 30):
        resource_type = "Virtual Machine"
        shape = "box3d"
        color = "darkcyan"
        
    clean_label = f"{concise_name}\n({resource_type})"
    return clean_label, shape, color

def get_clean_node_label(service_name):
    """Wrapper for backward compatibility, returns only the label."""
    label, _, _ = get_node_attributes(service_name)
    return label
    
# --- CORE GRAPHVIZ WRAPPERS ---

def add_edge(graph, source, target, relationship_type="", dir_type="forward", color="black", fontcolor="black"):
    """Adds a new edge to the graph if it doesn't already exist."""
    edge = (source, target, relationship_type, dir_type)
    if edge not in edges_set:
        # We always use the main graph (dot) to draw inter-cluster arcs
        graph.edge(source, target, label=relationship_type, dir=dir_type, color=color, fontcolor=fontcolor)
        edges_set.add(edge)

def edge_exists(source, target, relationship_type="", dir_type="forward"):
    """Checks if a specific edge configuration already exists in the set."""
    return (source, target, relationship_type, dir_type) in edges_set

def get_unprocessed_links(links, parent_node):
    """Return only the unprocessed links based on the link's name."""
    unprocessed_links = []
    sanitized_parent_node = sanitize_node_id(parent_node)
    for it_link in links:
        link_key = (sanitized_parent_node, it_link.link_type.name, it_link.name.obj)
        
        if link_key not in processed_links_set:
            unprocessed_links.append(it_link)
    return unprocessed_links

# --- DATABASE LOGIC ---
def connect_to_database(username, password, ip, port, database_name, collection_name):
    """
    Connects to MongoDB, clears the target collection, and returns the collection object.
    """
    try:
        client = MongoClient(f"mongodb://{ip}:{port}/")
    except Exception:
        client = MongoClient(f"mongodb://{username}:{password}@{ip}:{port}/")    

    db = client[database_name]
    collection = db[collection_name]
    collection.delete_many({}) # Clear collection on startup

    return collection 

def insert_data_database(collection, response, peer_hostname =None):
    """
    Inserts discovery data into MongoDB and tracks the node as visited using its sanitized ID.
    """
    sanitized_hostname = sanitize_node_id(peer_hostname)

    # We check if the response status is OK before doing anything
    is_response_ok = response.status == oc2.StatusCode.OK
    
    if sanitized_hostname not in nodes_visited and is_response_ok:
        m = Message()
        m.set(response)
        data = JSONEncoder().encode(m)
        parsed_data = json.loads(data)
        
        # Insert only the results into the database if status is 200
        if parsed_data['body']['openc2']['response']['status'] == 200:
            result = parsed_data['body']['openc2']['response']['results']['x-ctxd']
            collection.insert_one(result).inserted_id
        
        # CRITICAL: Add the sanitized ID to the visited set only if query succeeded (Status 200)
        nodes_visited.add(sanitized_hostname)
    elif not is_response_ok:
        # If query failed (e.g., 404), do not add to nodes_visited 
        logger.warning(f"Failed to query {peer_hostname}. Status: {response.status.name}")

# --- NEW GENERALIZED FUNCTION FOR INFERRED LINKS ---

def draw_inferred_links(dot, all_nodes):
    """
    Infers and draws general missing logical connections (VM-NIC, VNet-Resource, 
    Packet Flow, Load Balancer) after the explicit discovery process is complete.
    
    This version relies on naming conventions to infer resource types.
    """
    
    # 1. NODE COLLECTIONS BY TYPE (Based on naming conventions)
    
    # Map to find the NIC node from the VM name (e.g., kube-apiserver -> kube-apiserver_nic...)
    vm_to_nic = {}
    
    vnet_nodes = set()
    vm_nodes = set()
    nic_nodes = set()
    lb_nodes = set()
    vpn_nodes = set()

    # Identification and classification
    for node_id in all_nodes:
        # Use the original unsanitized name for cleaner classification, if possible
        # We replace the sanitization characters in reverse
        original_name = node_id.replace('_', ' ').replace('-', '.').replace('ANY', '*').lower()

        if 'vnet' in original_name or 'vn ' in original_name:
            vnet_nodes.add(node_id)
        elif 'nic' in original_name:
            nic_nodes.add(node_id)
            # Attempt to infer the VM name from the NIC
            # Example: kube-apiserver.nic.e2f15c63... -> kube-apiserver
            if '.nic.' in original_name:
                vm_part = original_name.split('.nic.')[0] 
            else: # Handle sanitized names like "kube-apiserver_nic..."
                vm_part = original_name.split(' nic')[0]
                
            vm_id = sanitize_node_id(vm_part)
            vm_to_nic[vm_id] = node_id # Map VM_ID -> NIC_ID
            
        # Classify as VM if not already NIC/GW/VNet
        if 'vm' in original_name or 'apiserver' in original_name or ('kubernetes' in original_name and 'internal' in original_name):
            vm_nodes.add(node_id)
            
        elif 'gw' in original_name and 'vpn' in original_name:
            vpn_nodes.add(node_id)
        elif 'lb' in original_name or 'loadbalancer' in original_name:
             lb_nodes.add(node_id) 
    
    # Add all inferred VMs that haven't been classified
    vm_nodes.update(set(vm_to_nic.keys()))


    # --- 2. LOGICAL LINK VM <-> NIC (attached_to) ---
    # Connect each VM to its corresponding NIC, if both exist
    for vm_id, nic_id in vm_to_nic.items():
        if vm_id in all_nodes and nic_id in all_nodes and not edge_exists(vm_id, nic_id, "attached_to", 'forward'):
            add_edge(dot, vm_id, nic_id, "attached_to", dir_type='forward', color='blue', fontcolor='blue')

    # --- 3. LOGICAL LINK VNet -> Resource (hosting) ---
    # Connect the VNet to all resources it should contain (VM, NIC, GW)
    if vnet_nodes:
        # Note: pop() works here assuming a single relevant VNet for simplicity.
        vnet_id = vnet_nodes.pop()
        
        all_network_resources = vm_nodes.union(nic_nodes).union(vpn_nodes)
        
        for resource_id in all_network_resources:
            # Ensure not to link the VNet to itself and that the link does not already exist
            if resource_id != vnet_id and not edge_exists(vnet_id, resource_id, 'hosting', 'forward'):
                add_edge(dot, vnet_id, resource_id, "hosting", dir_type='forward', color='teal', fontcolor='teal')

    # --- 4. PACKET FLOW LINK LOAD BALANCER -> Backend (packet_flow) ---
    if lb_nodes:
        lb_id = lb_nodes.pop() # Get the first LB found
        
        # Draw the Load Balancer node if it doesn't explicitly exist
        if lb_id not in all_nodes:
            dot.node(lb_id, f'Load Balancer', shape='Msquare', color='darkorange', fontcolor='darkorange')
            
        azure_id = sanitize_node_id("azure")
        if not edge_exists(azure_id, lb_id, "hosting", 'forward'):
            add_edge(dot, azure_id, lb_id, "hosting", dir_type='forward', color='gray', fontcolor='gray')

        # Connect the LB to all VMs (backend pool)
        for vm_id in vm_nodes:
            if vm_id != lb_id and not edge_exists(lb_id, vm_id, "packet_flow", 'forward'):
                 add_edge(dot, lb_id, vm_id, "packet_flow", dir_type='forward', color='darkorange', fontcolor='darkorange')
                 
    # --- 5. KEY INFERRED FLOW LINK (Based on Kubernetes/App communication logic) ---
    
    # k8s API Server <-> Internal Cluster Communication
    k_api_id = sanitize_node_id('kube-apiserver')
    k_internal_id = sanitize_node_id('kubernetes-internal')
    if k_api_id in all_nodes and k_internal_id in all_nodes and not edge_exists(k_api_id, k_internal_id, "packet_flow", 'both'):
        add_edge(dot, k_api_id, k_internal_id, "packet_flow", dir_type='both', color='orange', fontcolor='orange')

    # App VM (mindicity-miranda) <-> Associated Services (AllowFromFD/AllowDash)
    miranda_id = sanitize_node_id('mindicity-miranda')
    
    if miranda_id in all_nodes:
        # We use fixed names for resources that appear in the example graph (Contextual Inference)
        potential_partners = [sanitize_node_id('AllowFromFD'), sanitize_node_id('AllowDash')]
        
        for partner_id in potential_partners:
            if partner_id in all_nodes and not edge_exists(miranda_id, partner_id, "packet_flow", 'both'):
                add_edge(dot, miranda_id, partner_id, "packet_flow", dir_type='both', color='purple', fontcolor='purple')
    
    return

# --- CORE LOGIC ---

def recursive_process_links(links, cmd, pf, p, dot, parent_node):
    """
    Recursively processes links from the Actuator response to build the Graphviz graph.
    It handles node styling, clustering by Resource Group, and manages link processing.
    """
    # Sanitize the parent node name for consistency in DOT ID
    sanitized_parent_node = sanitize_node_id(parent_node)
    
    # Dictionary to hold Subgraphs (Resource Group Clusters)
    rg_graphs = {}

    # Helper function to get the correct Graphviz object (subgraph or main graph)
    def get_graph_context(resource_group_name, main_dot):
        if resource_group_name:
            if resource_group_name not in rg_graphs:
                # Create a new subgraph for the cluster
                subgraph_name = f'cluster_{sanitize_node_id(resource_group_name)}'
                # Using 'cluster_' which is recognized by Graphviz for visual grouping
                g = Digraph(subgraph_name, graph_attr={'label': f'RG: {resource_group_name}', 'style': 'filled', 'color': 'lightgrey'})
                rg_graphs[resource_group_name] = g
                main_dot.subgraph(g) # Adds the subgraph to the main graph
            return rg_graphs[resource_group_name]
        return main_dot # Return the main graph if an RG is not found
        
    # Helper function to get the current description content (Fixes the AttributeError)
    def get_description_content(link):
        desc = getattr(link, 'description', None)
        if desc is None:
            return ""
        
        # If it's an otupy object (e.g., Name, Description), access .obj
        if hasattr(desc, 'obj'):
            return desc.obj
        
        # If it's a standard Python string, use it directly
        return str(desc)
    
    # 1. Ensure the parent node is drawn (only if it's not the root Actuator 'azure')
    if sanitized_parent_node not in nodes_visited and parent_node != 'azure':
        # Get attributes for the parent node
        clean_label, node_shape, node_color = get_node_attributes(parent_node)
        dot.node(sanitized_parent_node, clean_label, shape=node_shape, color=node_color, fontcolor='black')


    for it_link in links:
        link_key = (sanitized_parent_node, it_link.link_type.name, it_link.name.obj)

        if link_key in processed_links_set:
            continue
        
        processed_links_set.add(link_key)
        
        # --- NEW: Extract Resource Group from Link Description ---
        resource_group_name = None
        link_description_content = get_description_content(it_link)
        
        if link_description_content and 'RG:' in link_description_content:
            try:
                # Assuming format 'RG:{RG_NAME} Tags:...'
                rg_part = [p for p in link_description_content.split(' ') if p.startswith('RG:')][0]
                resource_group_name = rg_part.split(':')[1]
            except Exception:
                pass 
        
        # Get the current drawing context (main graph or specific subgraph)
        current_graph = get_graph_context(resource_group_name, dot)


        # --- SPECIAL HANDLING 1: NSG -> RULE CONTAINMENT ARC (Invariant) ---
        if is_nsg_rule_link(it_link):
            
            peer_rule = next((p for p in it_link.peers if 'Rule:' in str(p.service_name.obj)), None)
            peer_nsg = next((p for p in it_link.peers if 'Rule:' not in str(p.service_name.obj)), None)
            
            if peer_rule and peer_nsg:
                peer_rule_name = str(peer_rule.service_name.obj)
                peer_nsg_name = str(peer_nsg.service_name.obj)
                
                source_node_id = sanitize_node_id(peer_nsg_name) 
                target_node_id = sanitize_node_id(peer_rule_name)

                relationship_label = extract_rule_label(peer_rule_name)
                edge_color = "darkgreen"
                edge_font_color = "darkgreen"
                dir_mode = 'forward'
                
                # Add the Rule node (Crucial because it is not an Actuator)
                if target_node_id not in nodes_visited:
                    # NSG Rules use the context of their NSG for clustering
                    rule_graph_context = get_graph_context(resource_group_name, dot) 
                    clean_label, node_shape, node_color = get_node_attributes(peer_rule_name)
                    rule_graph_context.node(target_node_id, clean_label, shape=node_shape, color=node_color, fontcolor=node_color)
                    nodes_visited.add(target_node_id) 
                    
                # Draw the custom arc on the main graph (dot) to ensure visibility
                if not edge_exists(source_node_id, target_node_id, relationship_label, dir_mode):
                    add_edge(dot, source_node_id, target_node_id, relationship_label, dir_type=dir_mode, color=edge_color, fontcolor=edge_font_color)
            
            continue
        # --- END NSG PARENT-CHILD HANDLING ---

        # --- STANDARD LOGIC FOR ALL OTHER LINKS ---
        
        # Style and direction for all standard Links
        relationship_label = str(it_link.link_type.name) 
        edge_color = "black"
        edge_font_color = "black"
        font_color = "black"
        text_color = None

        is_slpf = any('slpf' in str(p.service_name.obj).lower() for p in it_link.peers)
        if is_slpf:
            edge_color = "red" 
            edge_font_color = "red"
            text_color = "red"
            font_color = "red"
        
        dir_mode = 'forward'
        if relationship_label == 'packet_flow':
            dir_mode = 'both'
        elif relationship_label == 'hosting':
            dir_mode = 'back'
        elif relationship_label == 'protect':
             dir_mode = 'back'
        
        is_azure_root = (parent_node.lower() == 'azure') 
        peers_list = list(it_link.peers)

        # --- SPECIAL HANDLING 2: DIRECT CONNECTION LINKS (VM->NIC, NIC->NSG) ---
        if len(peers_list) == 2 and is_azure_root and relationship_label in ['packet_flow', 'protect']:
            
            peer_a_name = str(peers_list[0].service_name.obj)
            sanitized_a_id = sanitize_node_id(peer_a_name)
            
            peer_b_name = str(peers_list[1].service_name.obj)
            sanitized_b_id = sanitize_node_id(peer_b_name)
            
            # 2. Ensure nodes are drawn in their RG context
            for peer in peers_list:
                sanitized_id = sanitize_node_id(str(peer.service_name.obj))
                if sanitized_id not in nodes_visited:
                    clean_label, node_shape, node_color = get_node_attributes(str(peer.service_name.obj))
                    # Nodes are drawn in the link's context (i.e., the RG context)
                    current_graph.node(sanitized_id, clean_label, shape=node_shape, color=node_color, fontcolor='black')
            
            # 3. Draw the arc between Peer A and Peer B (The connection)
            if not edge_exists(sanitized_a_id, sanitized_b_id, relationship_label, dir_mode):
                edge_dir_mode = 'both' if relationship_label == 'packet_flow' else 'back'
                # Use the main graph (dot) to draw the arcs
                add_edge(dot, sanitized_a_id, sanitized_b_id, relationship_label, dir_type=edge_dir_mode, color=edge_color, fontcolor=edge_font_color)
            
            # 4. Also draw the Azure -> Peer A and Azure -> Peer B arc
            if not edge_exists(sanitized_parent_node, sanitized_a_id, 'hosting', 'forward'):
                add_edge(dot, sanitized_parent_node, sanitized_a_id, 'hosting', dir_type='forward', color='gray', fontcolor='gray')
            if not edge_exists(sanitized_parent_node, sanitized_b_id, 'hosting', 'forward'):
                add_edge(dot, sanitized_parent_node, sanitized_b_id, 'hosting', dir_type='forward', color='gray', fontcolor='gray')

            continue 
        # --- END DIRECT CONNECTION HANDLING ---


        # --- FINAL STANDARD LOGIC (Azure -> Resource) ---
        for it_peer in peers_list:

            peer_service_name = str(it_peer.service_name.obj)
            peer_hostname = peer_service_name
            sanitized_peer_id = sanitize_node_id(peer_hostname)
            
            # 1. DRAW THE NODE (UPDATED to use attributes and clustering context)
            clean_label, node_shape, node_color = get_node_attributes(peer_service_name)
            
            final_node_color = text_color if text_color else node_color
            final_font_color = font_color if font_color else 'black'

            if sanitized_peer_id not in nodes_visited:
                # Draw on the clustering context
                current_graph.node(sanitized_peer_id, clean_label, shape=node_shape, color=final_node_color, fontcolor=final_font_color)
                
                if not is_azure_root:
                    nodes_visited.add(sanitized_peer_id) 

            # 2. DRAW THE EDGE (parent_node -> peer)
            if not edge_exists(sanitized_parent_node, sanitized_peer_id, relationship_label, dir_mode):
                add_edge(dot, sanitized_parent_node, sanitized_peer_id, relationship_label, dir_type=dir_mode, color=edge_color, fontcolor=edge_font_color)

            # 3. RECURSION AND DATABASE CALL (ONLY for top-level links from Azure)
            if is_azure_root and sanitized_peer_id not in nodes_visited: 
                
                target_name = Name(peer_hostname)
                target_context = ctxd.Context(services=ArrayOf(Name)([target_name]), 
                                              links=ArrayOf(Name)()) 
                new_cmd = oc2.Command(action=oc2.Actions.query, target=target_context, args=cmd.args, actuator=cmd.actuator)

                tmp_resp = p.sendcmd(new_cmd)
                
                logger.info("Got response: %s", tmp_resp)
                
                insert_data_database(collection, tmp_resp, peer_hostname)
                
                pass 

    return

# --- MAIN EXECUTION LOGIC ---
def main(openstack_parameters, collection):
    """
    Initializes the OpenC2 Producer, sends the initial discovery query to the Azure Actuator,
    and starts the recursive graph building process.
    """
    logger.info("Creating Producer")

    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer(openstack_parameters['ip'],
                                                                          openstack_parameters['port'],
                                                                          openstack_parameters['endpoint']))
    
    actuator_asset_id = openstack_parameters['asset_id']
    pf = ctxd.Specifiers({'asset_id': actuator_asset_id})
    pf.fieldtypes['asset_id'] = actuator_asset_id
    
    arg = ctxd.Args({'name_only': False})
    context = ctxd.Context(services=ArrayOf(Name)(), links=ArrayOf(Name)())
    cmd = oc2.Command(action=oc2.Actions.query, target=context, args=arg, actuator=pf)

    logger.info("Sending command: %s", cmd)
    resp_openstack = p.sendcmd(cmd)

    insert_data_database(collection, resp_openstack, openstack_parameters['asset_id'])

    if not arg['name_only']:
        # Create the graph
        dot = Digraph("example_graph", graph_attr={'rankdir': 'LR'})
        # Add a stylized Azure root node
        dot.node('azure', 'Azure', shape='tripleoctagon', color='blue', fontcolor='blue') 
        
        # Start recursion from the Azure root node
        if 'results' in resp_openstack.content and 'links' in resp_openstack.content['results']:
            recursive_process_links(resp_openstack.content['results']['links'], cmd, pf, p, dot, 'azure')

        # --- CALL TO THE NEW GENERALIZED FUNCTION ---
        # Draw inferred links after all nodes have been visited.
        # nodes_visited is the global set of sanitized nodes discovered so far.
        draw_inferred_links(dot, nodes_visited)

        # Render and save the graph files
        dot.render(os.path.dirname(os.path.abspath(__file__))+'/azure_graph' , view=False)
        dot.save(os.path.dirname(os.path.abspath(__file__))+'/azure_graph.gv')

if __name__ == '__main__':
    
    configuration_file = os.path.dirname(os.path.abspath(__file__))+"/producers-configuration.json"
    with open(configuration_file, 'r') as file:
        configuration_parameters = json.load(file)

    collection = connect_to_database(username=configuration_parameters['mongodb']['username'],
                                     password=configuration_parameters['mongodb']['password'],
                                     ip = configuration_parameters['mongodb']['ip'],
                                     port = configuration_parameters['mongodb']['port'],
                                     database_name= configuration_parameters['mongodb']['database_name'],
                                     collection_name= configuration_parameters['mongodb']['collection_name'])

    for element in configuration_parameters['clusters']:
        if (element["type"] == "azure"):      
            main(element, collection) # start the discovery at the azure service