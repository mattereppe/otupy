#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import sys
from argparse import ArgumentParser

import otupy as oc2
from otupy.types.data.feature import Feature
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.fclm as fclm

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("openc2producer")


def main():

    arguments = ArgumentParser()
    arguments.add_argument("--start", action="store_true", help="Start monitoring")
    arguments.add_argument("--stop", help="Stop monitoring the specified process")
    arguments.add_argument("--query", action="store_true", help="Stop monitoring the specified process")
    arguments.add_argument("--probe", default="filebeat", help="Select probe to run [filebeat]")
    arguments.add_argument("--server", default="127.0.0.1", help="Select IP address of the Consumer")
    arguments.add_argument("--port", default="8080", help="Select TCP port of the Consumer")
    args = arguments.parse_args()

    Feature.extend("export_fields", 11)
    Feature.extend("exports_config", 12)
    Feature.extend("imports_config", 13)
    Feature.extend("import_controls", 14)
    logger.info("Creating Producer")

    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer(args.server, args.port))
    arg = fclm.Args({"response_requested": oc2.ResponseType.complete})
    pf = fclm.Specifiers({"asset_id": "fclm-filebeat"})

    if args.query:
        cmd = oc2.Command(
            oc2.Actions.query,
            oc2.Features(
                [
                    oc2.Feature.versions,
                    oc2.Feature.profiles,
                    oc2.Feature.pairs,
                    oc2.Feature.export_fields,
                    oc2.Feature.exports_config,
                    oc2.Feature.import_controls,
                    oc2.Feature.imports_config,
                ]
            ),
            arg,
            actuator=pf,
        )
    elif args.start:
        efs = oc2.ArrayOf(fclm.EF)()  # type: ignore
        efs.append(fclm.EF("timestamp"))
        efs.append(fclm.EF("metadata"))
        efs.append(fclm.EF("message"))
        efs.append(fclm.EF("log.file.path"))
        efs.append(fclm.EF("input.type"))
        a = fclm.Collector(address=oc2.IPv4Addr("192.1.1.6"), port=oc2.Port(1234), format=fclm.FileFormat.json)
        col = oc2.ArrayOf(fclm.Collector)()
        col.append(a)
        arg = fclm.Args(
            {
                # "start_time": oc2.DateTime(time.time() * 1000 + 5000),
                # "stop_time" :  oc2.DateTime(time.time() * 1000 + 10000),
                "exporter": fclm.Exporter(storage=oc2.File({"path": "httplogs", "name": "fb_out"})),
#                "exporter": fclm.Exporter(storage=oc2.File({"path": "test", "name": "fb_out"}), collectors=col),
                "import_controls": fclm.ImportOptions(scan_frequency=oc2.Duration(10), max_backoff=oc2.Duration(10)),
                "export_fields": efs,
            }
        )
        file = fclm.LogMonitor(oc2.File({"path": "/var/log/http_access.log"})) # Target (currently used)
        socket = fclm.LogMonitor(fclm.Socket("192.118.0.0", 1000, oc2.L4Protocol.tcp)) # Target
        uri = fclm.LogMonitor(oc2.URI("wwww.google.com")) # Target
        cmd = oc2.Command(oc2.Actions.start, file, arg, actuator=pf)

    elif args.stop:
      identifier = args.stop
      cmd = oc2.Command(oc2.Actions.stop, fclm.MonitorID(identifier), arg, actuator=pf)
    else:
        raise ValueError("Unsupported command")

    logger.info("Sending command: %s", cmd)
    resp = p.sendcmd(cmd)
    logger.info("Got response: %s", resp)

    if args.start:
        identifier = resp.content["results"]["monitor_id"]
        print("------------------------------")
        print("Started process: ", identifier)

    if args.query:
        print("------------------------------")
        print("Supported features:")
        for k,v in resp.content["results"].items():
            print(k, ":")
            if isinstance(v, list):
                for e in v:
                    print("\t- ", e)
            elif isinstance(v, dict):
                for l,u in v.items():
                   print("\t- ", l, ":", u)
            else:
                print("\t - ", v)


if __name__ == "__main__":
    main()
