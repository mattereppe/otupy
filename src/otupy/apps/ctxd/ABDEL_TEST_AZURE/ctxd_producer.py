#!/usr/bin/env python3

import os
import json
import logging
from graphviz import Digraph

import otupy as oc2
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("aks-discovery")

# --------------------------------------------------
# GLOBAL GRAPH STATE
# --------------------------------------------------
visited = set()          # visited node ids
nodes = {}               # node_id -> (label, type)
edges = set()            # (src, dst, type)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def sanitize(name: str) -> str:
    """Make a safe Graphviz node id."""
    return name.replace(" ", "_").replace("/", "_").replace(":", "_").replace(".", "_")

# --------------------------------------------------
# DISCOVERY
# --------------------------------------------------
def discover(node_name: str, producer: oc2.Producer, base_cmd: oc2.Command, parent_id=None):
    """
    Recursive discovery using PeerRole dynamically, no hard-coded numbers.
    parent_id is the node from which we discovered this node_name.
    """
    node_id = sanitize(node_name)



    # Build OpenC2 query
    target = Name(node_name)
    context = ctxd.Context(
        services=ArrayOf(Name)([target]),
        links=ArrayOf(Name)()
    )

    cmd = oc2.Command(
        action=oc2.Actions.query,
        target=context,
        args=base_cmd.args,
        actuator=base_cmd.actuator
    )

    response = producer.sendcmd(cmd)
    links = response.content.get("results", {}).get("links", [])

    for link in links:
        parent_id=str(link.name.obj)
        link_type =link.link_type
        for peer in link.peers:
            peer_name = str(peer.service_name.obj)
            peer_id = sanitize(peer_name)

            # Determine type dynamically based on PeerRole
            ntype = "unknown"
            if hasattr(peer, "role") and peer.role is not None:
                role_obj = peer.role
                # Use names, not numbers
                if role_obj.name in ["controlled"]:
                    ntype = "namespace"
                elif role_obj.name in ["guest"]:
                    ntype = "pod"
                elif role_obj.name in ["control"]:
                    ntype = "node"
                else:
                    ntype = "unknown"

            # store node if not already there
            nodes.setdefault(peer_id, (peer_name, ntype))
            edges.add((parent_id,peer_name,link_type.name))


            # Recurse passing current node as parent
            #discover(peer_name, producer, base_cmd, parent_id=node_id)


# --------------------------------------------------
# GRAPH RENDERING
# --------------------------------------------------
def render_graph(nodes, edges, output_name="aks_graph"):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Create graphs/ folder ---
    graph_dir = os.path.join(script_dir, "graphs")
    os.makedirs(graph_dir, exist_ok=True)

    output_path = os.path.join(graph_dir, output_name)
    dot = Digraph(
        "aks",
        engine="sfdp",
        graph_attr={
            "rankdir": "LR",
            "fontname": "Helvetica",
            "splines": "true",
            "overlap": "prism"
        }
    )

    # Node colors per type
    type_style = {
        "node": {"shape": "box3d", "color": "darkgreen"},
        "namespace": {"shape": "ellipse", "color": "darkblue"},
        "pod": {"shape": "box", "color": "black"},
        "service": {"shape": "diamond", "color": "orange"},
        "unknown": {"shape": "oval", "color": "gray"}
    }

    # Edge colors per type
    edge_colors = {
        "hosting": "brown",
        "control": "red",
        "packet_flow": "blue",
        "api": "purple",
        "protect": "brown"
    }

    # --- Add nodes ---
    for node_id, (label, ntype) in nodes.items():
        style = type_style.get(ntype, {"shape": "oval", "color": "gray"})
        dot.node(node_id, label, shape=style["shape"], color=style["color"])

    # --- Add edges ---
    for src, dst, etype in edges:
        color = edge_colors.get(etype, "black")
        dot.edge(src, dst, label=etype, color=color, dir="forward")

    # --- Render ---
    dot.render(output_path, format="pdf", view=False)
    dot.save(output_path + ".gv")
    print(f"Graph saved as {output_path}.pdf and {output_path}.gv")

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main(config):
    logger.info("Starting AKS discovery")

    producer = oc2.Producer(
        "producer.local",
        JSONEncoder(),
        HTTPTransfer(config["ip"], config["port"], config["endpoint"])
    )

    actuator_pf = ctxd.Specifiers({"asset_id": config["asset_id"]})
    actuator_pf.fieldtypes["asset_id"] = config["asset_id"]

    args = ctxd.Args({"name_only": False})

    base_cmd = oc2.Command(
        action=oc2.Actions.query,
        target=ctxd.Context(services=ArrayOf(Name)(), links=ArrayOf(Name)()),
        args=args,
        actuator=actuator_pf
    )

    # Start discovery
    discover("azure", producer, base_cmd)

    # Render graph
    render_graph(nodes=nodes, edges=edges)

    logger.info("Discovery completed")

# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------
if __name__ == "__main__":
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "producers-configuration.json")
    with open(config_file) as f:
        config = json.load(f)

    for cluster in config["clusters"]:
        if cluster["type"] == "azure":
            main(cluster)
