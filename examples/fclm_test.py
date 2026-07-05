#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import sys
import datetime
from argparse import ArgumentParser
from time import sleep

import otupy as oc2
from otupy.profiles.fclm.data.collector import Host
from otupy.types.data.feature import Feature
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.fclm as fclm

logging.basicConfig(stream=sys.stdout, level=logging.WARN)
logger = logging.getLogger("openc2producer")


def main():

    arguments = ArgumentParser()
    arguments.add_argument("--start", action="store_true", help="Start monitoring")
    arguments.add_argument("--stop", help="Stop monitoring the specified process")
    arguments.add_argument("--query", action="store_true", help="Stop monitoring the specified process")
    arguments.add_argument("--probe", default="filebeat", help="Select probe to run [filebeat]")
    arguments.add_argument("--server", default="127.0.0.1", help="Select IP address of the Consumer")
    arguments.add_argument("--port", default="8080", help="Select TCP port of the Consumer")
    arguments.add_argument("--test", type=int, default="1", help="Number of times to repeat a full cycle")
    args = arguments.parse_args()

    Feature.extend("export_fields", 11)
    Feature.extend("exports_config", 12)
    Feature.extend("imports_config", 13)
    Feature.extend("import_controls", 14)

    sum_start = 0
    sum_stop = 0
    for i in range(args.test):
#      print("Running test n. %s/%s", i, args.test)
  
      tstart = datetime.datetime.now()
      p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer(args.server, args.port))
      arg = fclm.Args({"response_requested": oc2.ResponseType.complete})
      pf = fclm.Specifiers({"asset_id": "fclm-filebeat"})

      if args.query:
        # Query features
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
        resp = p.sendcmd(cmd)
        tstop = datetime.datetime.now()
        diff = (tstop-tstart).total_seconds()
        sum_start = sum_start + diff

      else:
        # Start filebeat
        tstart = datetime.datetime.now()
        efs = oc2.ArrayOf(fclm.EF)()  # type: ignore
        efs.append(fclm.EF("timestamp"))
        efs.append(fclm.EF("metadata"))
        efs.append(fclm.EF("message"))
        efs.append(fclm.EF("log.file.path"))
        efs.append(fclm.EF("input.type"))
        a = fclm.Collector(host=Host("127.0.0.1"), port=oc2.Port(1234), format=fclm.FileFormat.json)
        col = oc2.ArrayOf(fclm.Collector)()
        col.append(a)
        arg = fclm.Args(
            {
                "exporter": fclm.Exporter(collectors=col),
                "import_controls": fclm.ImportOptions(scan_frequency=oc2.Duration(10), max_backoff=oc2.Duration(10)),
                "export_fields": efs,
            }
        )
        file = fclm.LogMonitor(oc2.File({"path": "/var/log/http_access.log"}))  # Target (currently used)
        cmd = oc2.Command(oc2.Actions.start, file, arg, actuator=pf)
    
        logger.info("Sending command: %s", cmd)
        resp = p.sendcmd(cmd)
        tstop = datetime.datetime.now()
        diff = (tstop-tstart).total_seconds()
        sum_start = sum_start + diff
  #      print("Time to start: ", diff)
        
        logger.info("Got response: %s", resp)
        identifier = resp.content["results"]["monitor_id"]
  #      print("------------------------------")
  #      print("Started process: ", identifier)
    
        sleep(3)
        # Stop filebeat
        arg = fclm.Args({"response_requested": oc2.ResponseType.complete})
        tstart = datetime.datetime.now()
        cmd = oc2.Command(oc2.Actions.stop, fclm.MonitorID(identifier), arg, actuator=pf)
    
        logger.info("Sending command: %s", cmd)
        resp = p.sendcmd(cmd)
        tstop = datetime.datetime.now()
        diff = (tstop-tstart).total_seconds()
        sum_stop = sum_stop + diff
  #      print("Time to stop: ", diff)
        logger.info("Got response: %s", resp)
    
        sleep(3)
  
    print("Average time to start/stop: ", sum_start/args.test, "\t", sum_stop/args.test)

if __name__ == "__main__":
    main()
