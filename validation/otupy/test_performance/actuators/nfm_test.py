"""This is a simple producer that can be used to test any NFM actuator.

Usage: <nfm_producer> [--start | --stop <id> | --query ]

--start returns the id of the nfm process. Take note of it and use it to stop the process later.

"""

import logging
import datetime
from time import sleep

from argparse import ArgumentParser

from otupy import Producer, Command, Actions, Features, Feature, Args, ResponseType, StatusCode, File
from otupy.types.data.uri import URI
from otupy.types.targets.file import File
from otupy.profiles.nfm import Exporter, Specifiers, MonitorID
from otupy.profiles.nfm import ExportOptions
from otupy.profiles.nfm.data.collector import Collector, Host
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
arguments.add_argument("--server", default="127.0.0.1", help="Select IP address of the Consumer")
arguments.add_argument("--port", default="8080", help="Select TCP port of the Consumer")
arguments.add_argument("--iface", default="eth0", help="Select interface to monitor")
arguments.add_argument("--test", type=int, default="1", help="Number of times to repeat a full cycle")
args = arguments.parse_args()

sum_start = 0
sum_stop = 0
for i in range(args.test):

  producer = Producer("nfm.example.net", JSONEncoder(), HTTPTransfer(args.server, args.port))
  arg = Args({"response_requested": ResponseType.complete})
  
  actuator = Specifiers({"asset_id": "nfm-" + args.probe})
  cmd = None
  
  # First, we do the query action.
  if args.query:
    tstart = datetime.datetime.now()
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
                  Feature.interfaces,
                  Feature.information_elements,
              ]
          ),
          arg,
          actuator=actuator,
      )
    resp = producer.sendcmd(cmd)
    tstop = datetime.datetime.now()
    diff = (tstop-tstart).total_seconds()
    sum_start = sum_start + diff
#print("Query time: ", diff)

#    print("------------------------------")
#    print("Supported features:")
#    for k, v in resp.content["results"].items():
#        print(k, ":")
#        if isinstance(v, list):
#            for e in v:
#                print("\t- ", e)
#        elif isinstance(v, dict):
#            for l, u in v.items():
#                print("\t- ", l, ":", u)
#        else:
#            print("\t - ", v)
  else:
  	# Then we try to start a flow monitor.
# print("Starting nfm actuator...")
    tstart = datetime.datetime.now()
    collectors = ArrayOf(Collector)()
    collectors.append(Collector(host=Host("127.0.0.1"), port=Port(2055)))
    if args.probe == "fprobe" or args.probe=="nprobe":
        # For fprobe.
        arg = nfm.Args(
            {
                "exporter": Exporter(collectors=collectors),
                "exporter_options": ExportOptions(format=FlowFormat.netflow5, timeout=60),
            }
        )
    if args.probe == "packetbeat":
        # For packetbeat.
        arg = nfm.Args(
            {
                "exporter": Exporter(storage=File(name="test", path="packetbeat-test"), collectors=collectors),
                "exporter_options": ExportOptions(format=FlowFormat.json, timeout=60),
            }
        )
    interfaces = ArrayOf(Interface)()
    interfaces.append(Interface(name=args.iface))
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
    resp = producer.sendcmd(cmd)
    identifier = resp.content["results"]["monitor_id"]
    tstop = datetime.datetime.now()
    diff = (tstop-tstart).total_seconds()
    sum_start = sum_start + diff
#print("Time to start: ", diff)


    sleep(3)
    # Stop filebeat
    tstart = datetime.datetime.now()
    arg = nfm.Args({"response_requested": ResponseType.complete})
    cmd = Command(
        Actions.stop, MonitorID(identifier), Args({"response_requested": ResponseType.complete}), actuator=actuator
    )
    resp = producer.sendcmd(cmd)
    tstop = datetime.datetime.now()
    diff = (tstop-tstart).total_seconds()
    sum_stop = sum_stop + diff
#print("Time to stop: ", diff)

    sleep(3)
  
print("\t  Start  \t  Stop  ")
print("No.\tSum\tAvg\tSum\tAvg")
print(args.test, "\t", sum_start, "\t",  sum_start/args.test, "\t", sum_stop, "\t", sum_stop/args.test)

