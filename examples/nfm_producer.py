""" This is a simple producer that can be used to test any NFM actuator.

	Usage: <nfm_producer> [--start | --stop <id> | --query ]

	--start returns the id of the nfm process. Take note of it and use it to stop the process later.

"""

import logging

from argparse import ArgumentParser

from otupy import Producer, Command, Actions, Features, Feature, Args, ResponseType, StatusCode, File
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

arguments = ArgumentParser()
arguments.add_argument("--start", action="store_true", help="Start monitoring")
arguments.add_argument("--stop", help="Stop monitoring the specified process")
arguments.add_argument("--query", action="store_true", help="Stop monitoring the specified process")
arguments.add_argument("--probe", default="fprobe", help="Select probe to run [fprobe|packetbeat]")
args = arguments.parse_args()

producer = Producer("nfm.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))
actuator = Specifiers({"asset_id": "nfm-"+args.probe})
# actuator = Specifiers({"asset_id": "nfm-packetbeat-example"})
arg = Args({"response_requested": ResponseType.complete})

# First, we do the query action.
if args.query:
    print("Querying features...")
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


# The we try to start a flow monitor.
if args.start:
    print("Starting nfm actuator...")
    collectors = ArrayOf(Collector)()
    collectors.append(Collector(address=IPv4Net("127.0.0.1"), port=Port(2055)))
    # For fprobe.
    arg = nfm.Args(
        {
            "exporter": Exporter(collectors=collectors),
            "exporter_options": ExportOptions(format=FlowFormat.netflow7),
        }
    )
    # For packetbeat.
    # arg = nfm.Args(
    #    {
    #        "exporter": Exporter(storage=File(name="test", path="/packetbeat-test")),
    #        "exporter_options": ExportOptions(format=FlowFormat.json),
    #    }
    # )
    interfaces = ArrayOf(Interface)()
    interfaces.append(Interface(name="en0"))
    ies = ArrayOf(IE)()
    ies.append(IE("source ip"))
    ies.append(IE("destination ip"))
    
    ipv4_connections = [
        # IPv4Connection(src_addr="192.168.1.1", dst_addr="130.251.17.2"),
    ]
    command = nfm.FlowMonitor(
        interfaces=interfaces, information_elements=ies, filter_v4=ArrayOf(IPv4Connection)(ipv4_connections)
    )
    
    cmd = Command(Actions.start, command, arg, actuator=actuator)


if args.stop:
    identifier = args.stop
    cmd = Command(
        Actions.stop, MonitorID(identifier), Args({"response_requested": ResponseType.complete}), actuator=actuator
    )

print("Command: ", cmd)
resp = producer.sendcmd(cmd)
print("Got: ", resp)

if args.query:
	assert resp.status == StatusCode.OK

if args.stop:
    identifier = resp.content["results"]["monitor_id"]


