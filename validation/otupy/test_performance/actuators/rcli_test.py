#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import hashlib
import datetime
from time import sleep
from argparse import ArgumentParser

import otupy as oc2
from otupy.types.data.uri import URI
from otupy.types.targets.file import File
from otupy.profiles.rcli import Files
from otupy.profiles.rcli.data.process import Process
from otupy.profiles.rcli.targets.processes import Processes

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.rcli as rcli

# logging.basicConfig(filename='openc2.log',level=logging.DEBUG)
"""logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('openc2producer')"""
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.WARNING)
# Create stdout handler for logging to the console
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))

hdls = [stdout_handler]
# Add both handlers to the logger
logger.addHandler(stdout_handler)
# Add file logger
file_handler = logging.FileHandler("controller_rcli_query_features.log")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True, datefmt="%t"))
logger.addHandler(file_handler)

def main():

    arguments = ArgumentParser()
    arguments.add_argument("--start", action="store_true", help="Start cli")
    arguments.add_argument("--stop", help="Stop process")
    arguments.add_argument("--copy", help="Copy file or url")
    arguments.add_argument("--delete", action="store_true", help="Delete file")
    arguments.add_argument("--query", action="store_true", help="Query features")
    arguments.add_argument("--cmd", default="", help="Run the given command [filebeat]")
    arguments.add_argument("--server", default="127.0.0.1", help="Select IP address of the Consumer [default=localhost]")
    arguments.add_argument("--port", default="8080", help="Select TCP port of the Consumer [default=8080]")
    arguments.add_argument("--test", type=int, default="1", help="Number of times to repeat a full cycle")
    args = arguments.parse_args()

    logger.info("Creating Producer")
    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer(args.server, args.port))

    pf = rcli.Specifiers({"asset_id": "rcli-example"})
    arg = rcli.Args({"response_requested": oc2.ResponseType.complete})

    sum_start = 0
    sum_stop = 0
    for i in range(args.test):
        if args.query:
            tstart = datetime.datetime.now()
            cmd = oc2.Command(oc2.Actions.query, oc2.Features([oc2.Feature.clicommands]), arg, actuator=pf)
            resp = p.sendcmd(cmd)
            tstop = datetime.datetime.now()
            diff = (tstop-tstart).total_seconds()
            sum_start = sum_start + diff
        elif args.start:
            tstart = datetime.datetime.now()
            command = Process(name="fprobe", command_line="-l 2 -i ens18 localhost:4555")
            procs = Processes()
            procs.append(command)
    #        procs.append(command2)
            cmd = oc2.Command(oc2.Actions.start, procs, arg, actuator=pf)
            resp = p.sendcmd(cmd)
            pid = resp.content['results']['process_status'][0]['pid']
            tstop = datetime.datetime.now()
            diff = (tstop-tstart).total_seconds()
            sum_start = sum_start + diff

            sleep(3)

            tstart = datetime.datetime.now()
            processes = Processes()
            processes.append(Process(pid=pid))
            cmd = oc2.Command(oc2.Actions.stop, processes, arg, actuator=pf)
            resp = p.sendcmd(cmd)
            tstop = datetime.datetime.now()
            diff = (tstop-tstart).total_seconds()
            sum_stop = sum_stop + diff
        elif args.copy:
            tstart = datetime.datetime.now()
            arg = rcli.Args(
                {
                    "storage": File({"path": "/test", "name": "mymessage.bin"}),
                }
            )
        
            with open(args.copy, 'rb') as f:
                bcontent = f.read()
        
            h = oc2.Hashes({"md5": oc2.Binaryx(hashlib.md5(bcontent).digest())})
            a = oc2.Artifact(
                mime_type="application/json",
    #            payload=oc2.Payload(URI(uri)),
                 payload=oc2.Binary(bcontent),
                 hashes= h
            )
            cmd = oc2.Command(oc2.Actions.copy, a, arg, actuator=pf)
            resp = p.sendcmd(cmd)
            tstop = datetime.datetime.now()
            diff = (tstop-tstart).total_seconds()
            sum_start = sum_start + diff

            sleep(3)

            tstart = datetime.datetime.now()
            arg = rcli.Args({"response_requested": oc2.ResponseType.complete})
            files = Files()
            files.append(File({"path": "/test", "name": "mymessage.bin"}))
            cmd = oc2.Command(oc2.Actions.delete, files, arg, actuator=pf)
            resp = p.sendcmd(cmd)
            tstop = datetime.datetime.now()
            diff = (tstop-tstart).total_seconds()
            sum_stop = sum_stop + diff
    

    print("\t  Start  \t  Stop  ")
    print("No.\tSum\tAvg\tSum\tAvg")
    print(args.test, "\t", sum_start, "\t",  sum_start/args.test, "\t", sum_stop, "\t", sum_stop/args.test)



if __name__ == "__main__":
    main()
