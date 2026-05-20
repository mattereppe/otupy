"""
CTXd context discovery — Graphviz renderer.

Install:
    pip install graphviz
    sudo apt install graphviz

Run:
    python discovery.py
    python discovery.py --save infra --format svg
    python discovery.py --layout fdp
    python discovery.py --no-show
"""

import argparse
import logging
import re
import time

from graphviz import Digraph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# All nodes are circles; border color encodes the service type.
# Fill is always white, label always black.
# ---------------------------------------------------------------------------
#
#   cloud   -> red   border  (root, most important)
#   execenv -> black border  (physical node)
#   host    -> blue  border  (VM / container)
#   netnode -> grey  border  (interface list, secondary)
#   network -> black border, dashed  (bridge)
#   unknown -> grey  border
#
_NODE_STYLE = {
    'cloud':   {'shape': 'circle', 'style': 'filled,bold',   'fillcolor': 'white', 'color': '#CC0000', 'fontcolor': 'black', 'penwidth': '3.0'},
    'execenv': {'shape': 'circle', 'style': 'filled,bold',   'fillcolor': 'white', 'color': '#111111', 'fontcolor': 'black', 'penwidth': '2.5'},
    'host':    {'shape': 'circle', 'style': 'filled',        'fillcolor': 'white', 'color': '#1A5DAD', 'fontcolor': 'black', 'penwidth': '2.0'},
    'netnode': {'shape': 'circle', 'style': 'filled,dashed', 'fillcolor': 'white', 'color': '#888888', 'fontcolor': '#555555', 'penwidth': '1.2'},
    'network': {'shape': 'circle', 'style': 'filled',        'fillcolor': 'white', 'color': '#111111', 'fontcolor': 'black', 'penwidth': '1.8'},
    'unknown': {'shape': 'circle', 'style': 'filled',        'fillcolor': 'white', 'color': '#AAAAAA', 'fontcolor': '#555555', 'penwidth': '1.0'},
}

# Edge styles: (color, style, arrowhead, dir)
_EDGE_STYLE = {
    'hosting':     ('#CC0000', 'solid',  'normal', 'back'),
    'packet_flow': ('#1A5DAD', 'dashed', 'open',   'both'),
    'controlling': ('#111111', 'dotted', 'vee',    'forward'),
    'protecting':  ('#CC0000', 'dashed', 'diamond','forward'),
    'subservice':  ('#AAAAAA', 'dotted', 'open',   'forward'),
}
_EDGE_DEFAULT = ('#888888', 'solid', 'normal', 'forward')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_id(sid_str: str) -> str:
    return re.sub(r'[:/\-@.]', '_', sid_str)


def _type_and_subtype(sid_str: str) -> tuple[str, str]:
    try:
        head = sid_str.split('/')[0]
        parts = head.split(':')
        return parts[0], (parts[1] if len(parts) > 1 else "")
    except Exception:
        return "unknown", ""


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(results: dict, *, engine: str = 'dot', fmt: str = 'pdf') -> Digraph:
    dot = Digraph(
        name='CTXd infrastructure',
        engine=engine,
        format=fmt,
    )
    dot.attr(
        rankdir='LR',
        fontname='Helvetica',
        fontsize='11',
        pad='0.8',
        nodesep='0.7',
        ranksep='1.4',
        overlap='false',
        splines='polyline',
    )
    dot.attr('node', fontname='Helvetica', fontsize='10')
    dot.attr('edge', fontname='Helvetica', fontsize='8')

    services = results.get('services', [])
    links    = results.get('links', [])

    sid_to_service: dict[str, object] = {str(svc.sid): svc for svc in services}

    # ------------------------------------------------------------------
    # 1. Register nodes grouped by type
    # ------------------------------------------------------------------
    seen_nodes: set[str] = set()
    type_buckets: dict[str, list[tuple[str, str]]] = {}
    # Keep track of the cloud node safe_id so we can anchor it centrally
    cloud_safe_ids: list[str] = []

    def _register_node(sid_str: str, label: str) -> str:
        safe_id = _sanitize_id(sid_str)
        if safe_id in seen_nodes:
            return safe_id
        seen_nodes.add(safe_id)
        type_, _ = _type_and_subtype(sid_str)
        type_buckets.setdefault(type_, []).append((safe_id, label))
        if type_ == 'cloud':
            cloud_safe_ids.append(safe_id)
        return safe_id

    for svc in services:
        _register_node(str(svc.sid), str(svc.name))

    # ------------------------------------------------------------------
    # 2. Collect edges — deduplicated
    # ------------------------------------------------------------------
    edges_seen: set[tuple[str, str, str]] = set()

    def _add_edge(src_safe: str, tgt_safe: str, ltype: str, peer_role: str = '') -> None:
        key = (src_safe, tgt_safe, ltype)
        if key in edges_seen:
            return
        edges_seen.add(key)

        color, style, arrowhead, direction = _EDGE_STYLE.get(ltype, _EDGE_DEFAULT)

        if ltype == 'hosting' and peer_role == 'host':
            direction = 'back'
        elif ltype == 'packet_flow':
            direction = 'both'

        dot.edge(
            src_safe, tgt_safe,
            xlabel=ltype,
            color=color,
            fontcolor=color,
            style=style,
            arrowhead=arrowhead,
            dir=direction,
            penwidth='2.0' if ltype == 'hosting' else '1.3',
        )

    # 2a. Subservice edges (host -> netnode), skip cloud->execenv
    # since the hosting link already covers that relationship
    for svc in services:
        if svc.subservices is None:
            continue
        src_sid = str(svc.sid)
        src_type, _ = _type_and_subtype(src_sid)
        if src_type == 'cloud':
            continue   # hosting link covers this, avoid double edge
        src_safe = _sanitize_id(src_sid)
        for sub_sid_obj in svc.subservices:
            sub_sid_str = str(sub_sid_obj)
            if sub_sid_str not in sid_to_service:
                logger.warning("Subservice SId not found: %s", sub_sid_str)
                continue
            tgt_safe = _sanitize_id(sub_sid_str)
            _add_edge(src_safe, tgt_safe, 'subservice')

    # 2b. Explicit link edges
    for lnk in links:
        src_sid = str(lnk.sid)
        src_safe = _sanitize_id(src_sid)

        if src_safe not in seen_nodes:
            _register_node(src_sid, str(lnk.name))
            logger.warning("Implicit source node: %s", src_sid)

        if lnk.peers is None:
            continue

        ltype = str(lnk.link_type) if lnk.link_type is not None else ""

        for peer in lnk.peers:
            tgt_sid = str(peer.sid)
            tgt_safe = _sanitize_id(tgt_sid)
            peer_role = str(peer.role) if peer.role is not None else ""

            if tgt_safe not in seen_nodes:
                _register_node(tgt_sid, str(peer.service_name))
                logger.warning("Implicit target node: %s", tgt_sid)

            _add_edge(src_safe, tgt_safe, ltype, peer_role)

    # ------------------------------------------------------------------
    # 3. Render nodes in clusters, cloud forced to center via rank trick:
    #    - cloud gets its own subgraph with rank=source
    #    - all other types rendered normally around it
    # ------------------------------------------------------------------

    # Cloud first, in a dedicated invisible subgraph to anchor layout
    if cloud_safe_ids:
        with dot.subgraph(name='cluster_cloud') as sg:
            sg.attr(
                label='cloud',
                style='rounded,dashed',
                color='#DDDDDD',
                fontname='Helvetica',
                fontsize='9',
                fontcolor='#CC0000',
                rank='source',         # forces cloud to the leftmost rank
            )
            style = _NODE_STYLE['cloud']
            for safe_id, label in type_buckets.get('cloud', []):
                sg.node(safe_id, label=label, **style)

    # All other types
    for ntype, node_list in type_buckets.items():
        if ntype == 'cloud':
            continue   # already rendered above
        style = _NODE_STYLE.get(ntype, _NODE_STYLE['unknown'])
        with dot.subgraph(name=f'cluster_{ntype}') as sg:
            sg.attr(
                label=ntype,
                style='rounded,dashed',
                color='#DDDDDD',
                fontname='Helvetica',
                fontsize='9',
                fontcolor='#555555',
            )
            for safe_id, label in node_list:
                sg.node(safe_id, label=label, **style)

    logger.info("Graph built: %d nodes, %d edges", len(seen_nodes), len(edges_seen))
    return dot


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_graph(dot: Digraph, *, outfile: str = 'ctxd_graph', show: bool = True) -> None:
    out = dot.render(filename=outfile, cleanup=True, view=show)
    logger.info("Rendered → %s", out)


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def _log_context(ctx):
    try:
        tot_services = tot_links = 0
        for type_ in ctx.keys():
            for item in ctx[type_]:
                if 'service' in item:
                    sub = ""
                    if item['service'].subservices is not None:
                        for s in item['service'].subservices:
                            sub += str(s) + ","
                    logger.debug("Service: %s [%s] {%s}",
                                 item['service'].sid, item['service'].name, sub)
                    tot_services += 1
                if 'link' in item:
                    if item['link'].peers is not None:
                        peers = ""
                        for p in item['link'].peers:
                            peers += (str(p.sid) + "@" + str(p.consumer)
                                      + " [" + str(p.role) + "], ")
                        logger.debug("Link: %s [%s] -- (%s) --> {%s}",
                                     item['link'].sid, item['link'].role,
                                     item['link'].link_type, peers)
                        tot_links += 1
        logger.info("Found %d service(s), %d link(s)", tot_services, tot_links)
    except Exception:
        logger.info("No service/link found!")


def loop(num=0, freq=0, event=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal num, freq
            while num != 0 and (event is None or not event.is_set()):
                func(*args, **kwargs)
                num -= 1
                if num != 0:
                    time.sleep(freq)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(outfile='ctxd_graph', layout='dot', fmt='pdf', show=True):
    import otupy
    import otupy.encoders
    import otupy.actuators
    from otupy.encoders.json import JSONEncoder
    import otupy.profiles.ctxd as ctxd
    from otupy.profiles.ctxd.data.name import Name
    from otupy.transfers.http.http_transfer import HTTPTransfer

    producer = otupy.Producer(
        "ctxd-discovery.mirandaproject.eu",
        JSONEncoder(),
        HTTPTransfer("127.0.0.1", 8080),
    )
    actuator_spec = ctxd.Specifiers({'asset_id': "ctxd-proxmox-example"})
    arg    = ctxd.Args({'name_only': False, 'cached': False})
    target = ctxd.Context(
        services=otupy.ArrayOf(Name)(),
        links=otupy.ArrayOf(Name)(),
    )
    cmd = otupy.Command(
        action=otupy.Actions.query,
        target=target,
        args=arg,
        actuator=actuator_spec,
    )

    try:
        context = producer.sendcmd(cmd)
        logger.info("Got response from: %s", context.from_)
        if context.status != otupy.StatusCode.OK:
            logger.warning("Unable to query %s: %s",
                           actuator_spec, context.content.get('status_text'))
            return
        results = context.content['results']
    except Exception as e:
        logger.warning("No context available from %s: %s", actuator_spec, e)
        return

    dot = build_graph(results, engine=layout, fmt=fmt)
    render_graph(dot, outfile=outfile, show=show)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="CTXd context discovery — Graphviz renderer")
    parser.add_argument("--save",   metavar="NAME", default="ctxd_graph")
    parser.add_argument("--format", dest="fmt", default="pdf",
                        choices=["pdf", "svg", "png"])
    parser.add_argument("--layout", default="dot",
                        choices=["dot", "neato", "fdp", "circo", "twopi"])
    parser.add_argument("--no-show", dest="show", action="store_false")
    args = parser.parse_args()
    main(outfile=args.save, layout=args.layout, fmt=args.fmt, show=args.show)