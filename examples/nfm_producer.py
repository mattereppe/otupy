"""This is a simple producer that can be used to test any NFM actuator."""

import logging

from otupy import Producer, Command, Actions, Features, Feature, Args, ResponseType, StatusCode
from otupy.types.data.uri import URI
from otupy.types.targets.file import File
from otupy.profiles.nfm import Exporter, Specifiers, MonitorID
from otupy.profiles.nfm import ExportOptions
from otupy.profiles.nfm.data.collector import Collector
from otupy.profiles.nfm import FlowFormat
from otupy.types.base import Record, ArrayOf, Array
from otupy.types.data import IPv4Addr, IPv6Addr, Port
from otupy.types.targets import MACAddr, IPv4Net
from otupy.profiles.nfm.data.ie import IE
from otupy.profiles.nfm import Interface
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.types.targets import IPv4Connection, IPv6Connection
from otupy.types.data.l4_protocol import L4Protocol
from otupy.actuators.nfm.nfm_actuator import NFMActuator  # Necessary for extending the features.

import otupy.profiles.nfm as nfm


producer = Producer("nfm.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))
actuator = Specifiers({"asset_id": "nfm-fprobe-example"})
arg = Args({"response_requested": ResponseType.complete})

# First, we do the query action.
cmd = Command(
    Actions.query,
    Features(
        [
            Feature.versions,
            Feature.profiles,
            Feature.pairs,
            Feature.exports,
            Feature.export_options,
            Feature.flow_format,
            Feature.filters,
        ]
    ),
    arg,
    actuator=actuator,
)
resp = producer.sendcmd(cmd)
assert resp.status == StatusCode.OK

# The we try to start a flow monitor.
collectors = ArrayOf(Collector)()
collectors.append(Collector(address=IPv4Net("127.0.0.1"), port=Port(2055)))
arg = nfm.Args(
    {
        "exporter": Exporter(collectors=collectors),
        "exporter_options": ExportOptions(format=FlowFormat.netflow7),
    }
)
interfaces = ArrayOf(Interface)()
interfaces.append(Interface(name="en0"))
ies = ArrayOf(IE)()
ies.append(IE("source ip"))
ies.append(IE("destination ip"))

ipv4_connections = [
    IPv4Connection(src_addr="192.168.1.1", dst_addr="130.251.17.2"),
]
command = nfm.FlowMonitor(
    interfaces=interfaces, information_elements=ies, filter_v4=ArrayOf(IPv4Connection)(ipv4_connections)
)

cmd = Command(Actions.start, command, arg, actuator=actuator)
resp = producer.sendcmd(cmd)
identifier = resp.content["results"]["monitor_id"]
print(resp, identifier)

cmd = Command(
    Actions.stop, MonitorID(identifier), Args({"response_requested": ResponseType.complete}), actuator=actuator
)
resp = producer.sendcmd(cmd)
print(resp)
